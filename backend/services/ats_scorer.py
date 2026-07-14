import re
import spacy
import numpy as np
from sentence_transformers import SentenceTransformer
from typing import Dict, List, Optional, Tuple

from backend.utils.file_utils import log_warning
from backend.core.config import SENTENCE_TRANSFORMER_MODEL
from backend.utils.matching import fuzzy_match_keywords
import re
def normalize_text(text: str) -> str:
    text = text.lower()
    text = text.replace("-", "")
    text = text.replace("_", "")
    text = text.replace("/", "")
    text = text.replace(" ", "")
    text = re.sub(r"[^a-z0-9]", "", text)
    return text
ZIP_CODE_PATTERN = r'\b\d{5}(?:-\d{4})?\b'

STREET_ADDRESS_PATTERN = (
    r'\b\d+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+'
    r'(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr|Court|Ct|Circle|Cir|Way|Place|Pl)\b'
)

def _tier_score(n: float, tiers:list)-> float:
    for threshold, pts in tiers:
        if n>=threshold:
            return pts
    
    return 0.0

#Location/privacy detection
def detect_location_info(text: str, nlp: spacy.Language) -> Dict:
    locations = []

    #method01: spacy NER
    doc = nlp(text)
    for ent in doc.ents:
        if ent.label_ in ['GPE', 'LOC']:
            locations.append({'text': ent.text, 'type': ent.label_.lower(), 'start': ent.start_char})

    #moetod02: street address regx
    for match in re.finditer(STREET_ADDRESS_PATTERN, text, re.IGNORECASE):
        locations.append({'text': match.group(), 'type': 'address', 'start': match.start()})

    #method03: ZIP/PIN CODE REGEX PATTERN
    for match in re.finditer(ZIP_CODE_PATTERN, text):
        locations.append({'text': match.group(), 'type': 'zip', 'start': match.start()})

    has_address = any(loc['type'] == 'address' for loc in locations)
    has_zip     = any(loc['type'] == 'zip'     for loc in locations)

    if has_address and has_zip:
        privacy_risk, penalty = 'high', 5.0
    elif has_address or has_zip:
        privacy_risk, penalty = 'high', 4.0
    elif len(locations) > 3:
        privacy_risk, penalty = 'medium', 3.0
    elif locations:
        privacy_risk, penalty = 'low', 2.0
    else:
        privacy_risk, penalty = 'none', 0.0

    recommendations = []
    if not locations:
        recommendations.append(" No privacy concerns detected.")
    if has_address:
        recommendations.append(" Remove full street addresses — ATS systems don't need this and it's a privacy risk.")
    if has_zip:
        recommendations.append(" Remove zip codes — this level of location detail is unnecessary.")
    if privacy_risk in ('low', 'medium') and not has_address and not has_zip:
        recommendations.append(" Consider reducing location mentions. 'City, State' in the contact header is sufficient.")

    return {
        'location_found':     len(locations) > 0,
        'detected_locations': locations,
        'privacy_risk':       privacy_risk,
        'recommendations':    recommendations,
        'penalty_applied':    penalty,
    }

def _calculate_semantic_similarity(skill: str, text: str, embedder: SentenceTransformer) -> float:
    #similarity = (A · B) / (|A| × |B|)
    if not skill or not text:
        return 0.0
    try:
        skill_vec  = embedder.encode(skill, convert_to_tensor=False)
        text_vec   = embedder.encode(text,  convert_to_tensor=False)

        similarity = np.dot(skill_vec, text_vec) / (
            np.linalg.norm(skill_vec) * np.linalg.norm(text_vec)
        )

        return float(max(0.0, min(1.0, similarity)))
    except Exception as e:
        log_warning(f"Similarity error for '{skill}': {e}", context='ats_scorer')
        return 0.0

def _skill_matches(
    skill: str,
    text: str,
    embedder: SentenceTransformer,
    threshold: float = 0.45,
) -> Tuple[bool, float]:

    skill_norm = re.sub(r"[^a-z0-9]", "", skill.lower())
    text_norm = re.sub(r"[^a-z0-9]", "", text.lower())

    # Exact match
    if skill_norm in text_norm:
        return True, 1.0

    # Word match
    for word in text.lower().split():
        word_norm = re.sub(r"[^a-z0-9]", "", word)
        if word_norm == skill_norm:
            return True, 1.0

    # Semantic similarity
    sim = _calculate_semantic_similarity(skill, text, embedder)

    return sim >= threshold, sim
def validate_skills_with_projects(
    skills: List[str],
    projects: List[Dict],
    experience_entries: List[Dict],
    embedder: SentenceTransformer,
    threshold: float = 0.6,
) -> Dict:

    if not skills:
        return {
            "validated_skills": [],
            "unvalidated_skills": [],
            "validation_percentage": 0.0,
            "skill_project_mapping": {},
            "validation_score": 0.0,
        }

    # Build experience text
    experience_text = " ".join(
        f"{e.get('job_title','')} {e.get('company','')} {e.get('description','')}"
        for e in experience_entries
        if isinstance(e, dict)
    )

    experience_normalized = normalize_text(experience_text)

    # Preprocess project texts once
    processed_projects = []

    for project in projects:
        text = f"{project.get('title','')} {project.get('description','')}"
        processed_projects.append({
            "title": project.get("title", "Untitled Project"),
            "text": text,
            "normalized": normalize_text(text)
        })

    validated_skills = []
    unvalidated_skills = []
    skill_project_mapping = {}
    print("=" * 60)
    print("Extracted Skills:")
    print(skills)

    print("=" * 60)
    print("Projects:")
    print(projects)

    print("=" * 60)
    print("Experience:")
    print(experience_entries)

    for skill in skills:

        normalized_skill = normalize_text(skill)

        matching_projects = []
        max_similarity = 0.0
        validated = False

        # --------------------------------------------------
        # STEP 1 : Exact Match (Fast)
        # --------------------------------------------------
        for project in processed_projects:

            if normalized_skill in project["normalized"]:
                matching_projects.append(project["title"])
                max_similarity = 1.0
                validated = True

        if normalized_skill in experience_normalized:

            if "Experience Section" not in matching_projects:
                matching_projects.append("Experience Section")

            max_similarity = max(max_similarity, 1.0)
            validated = True

        # --------------------------------------------------
        # STEP 2 : Semantic Match (Fallback)
        # --------------------------------------------------
        if not validated:

            for project in processed_projects:

                matched, similarity = _skill_matches(
                    skill,
                    project["text"],
                    embedder,
                    threshold,
                )

                max_similarity = max(max_similarity, similarity)

                if matched:
                    validated = True

                    if project["title"] not in matching_projects:
                        matching_projects.append(project["title"])

            if experience_text:

                matched, similarity = _skill_matches(
                    skill,
                    experience_text,
                    embedder,
                    threshold,
                )

                max_similarity = max(max_similarity, similarity)

                if matched:

                    validated = True

                    if "Experience Section" not in matching_projects:
                        matching_projects.append("Experience Section")

        # --------------------------------------------------
        # Save Results
        # --------------------------------------------------
        if validated:

            validated_skills.append({
                "skill": skill,
                "projects": matching_projects,
                "similarity": round(max_similarity, 3),
            })

            skill_project_mapping[skill] = matching_projects

        else:

            unvalidated_skills.append(skill)
            skill_project_mapping[skill] = []

    validation_percentage = (
        len(validated_skills) / len(skills)
        if skills else 0
    )

    # Better scoring
    if validation_percentage >= 0.90:
        validation_score = 15

    elif validation_percentage >= 0.80:
        validation_score = 13

    elif validation_percentage >= 0.70:
        validation_score = 11

    elif validation_percentage >= 0.60:
        validation_score = 9

    elif validation_percentage >= 0.50:
        validation_score = 7

    elif validation_percentage >= 0.40:
        validation_score = 5

    elif validation_percentage >= 0.30:
        validation_score = 3

    else:
        validation_score = 1
    print("="*50)
    print("Validated Skills")
    print(len(validated_skills))
    print(validated_skills)

    print("="*50)
    print("Unvalidated Skills")
    print(len(unvalidated_skills))
    print(unvalidated_skills)

    print("="*50)
    print(validation_percentage)
    print(validation_score)
    print("\n========== SKILL VALIDATION DEBUG ==========")
    print(f"Total Skills: {len(skills)}")
    print(f"Validated Skills: {len(validated_skills)}")
    print(f"Validation Percentage: {validation_percentage}")
    print(f"Validation Score: {validation_score}")

    print("\nValidated:")
    for s in validated_skills:
        print(s)

    print("\nUnvalidated:")
    for s in unvalidated_skills:
        print(s)

    print("============================================\n")
    return {
        "validated_skills": validated_skills,
        "unvalidated_skills": unvalidated_skills,
        "validation_percentage": round(validation_percentage, 2),
        "skill_project_mapping": skill_project_mapping,
        "validation_score": validation_score,
    }
#01: formatting score
def _calc_formatting_score(parsed_resume: Dict, text: str) -> float:

    score = 0.0

    exp_entries  = [e for e in parsed_resume.get('experience', []) if isinstance(e, dict)]
    edu_entries  = [e for e in parsed_resume.get('education', [])  if isinstance(e, dict)]
    skills       = parsed_resume.get('skills', [])
    summary      = parsed_resume.get('professional_summary', '')
    proj_entries = [p for p in parsed_resume.get('projects', [])   if isinstance(p, dict)]

    if exp_entries and any(e.get('job_title') or e.get('description') for e in exp_entries):
        score += 3.0
    if edu_entries:
        score += 2.0
    if len(skills) >= 3:
        score += 2.0
    if len(summary) > 30:
        score += 1.5
    if proj_entries:
        score += 1.5

    bullet_count = sum(
        1 for line in text.split('\n')
        if re.match(r'^\s*[•\-\*\◦]', line) or re.match(r'^\s*\d+\.', line)
    )
    score += _tier_score(bullet_count, [(15,5.0),(10,4.0),(5,3.0),(3,2.0),(1,1.0)])

    filled = sum(1 for has_it in [
        bool(exp_entries), bool(edu_entries), bool(skills),
        bool(summary.strip()), bool(proj_entries),
    ] if has_it)
    score += _tier_score(filled, [(4,5.0),(3,4.0),(2,3.0),(1,2.0)])

    return min(20.0, max(0.0, score))

#02 keyword score
def _calc_keywords_score(
    resume_keywords: List[str],
    skills: List[str],
    jd_keywords: Optional[List[str]] = None,
) -> float:

    all_resume_terms = list(set(
        [x.strip().lower() for x in (resume_keywords + skills) if x.strip()]
    ))

    if not jd_keywords:
        # No JD → evaluate resume richness only.
        # NOTE: rescaled to the same 0-25 max as the JD-match branch below.
        # (Previously this topped out at 20.0 while calculate_overall_score()
        # always divided by 25.0, so a no-JD resume could never score above
        # 80% on this dimension no matter how strong it was.)
        unique_terms = len(all_resume_terms)

        if unique_terms >= 25:
            return 25.0
        elif unique_terms >= 20:
            return 21.3
        elif unique_terms >= 15:
            return 17.5
        elif unique_terms >= 10:
            return 12.5
        else:
            return 7.5

    jd_terms = list(set(
        [x.strip().lower() for x in jd_keywords if x.strip()]
    ))

    fuzzy_result = fuzzy_match_keywords(
        all_resume_terms,
        jd_terms,
        threshold=75,
    )

    matched = len(fuzzy_result["matched"])
    total = len(jd_terms)

    match_percentage = matched / total if total else 0

    return round(match_percentage * 25, 1)
#3. CONTENT QUALITY SCORE
def _calc_content_score(
    text: str,
    action_verbs: List[str],
    grammar_results: Dict,
) -> float:
    
    score = 0.0

    score += _tier_score(len(action_verbs), [(15,10.0),(10,8.0),(7,6.0),(5,4.0),(3,2.0)])

    number_patterns = [
        r'\d+%',
        r'\$\d+',
        r'\d+[kKmMbB]',
        r'\d+\s*(?:users|customers|clients|projects|hours|days|months|years)',
        r'(?:increased|decreased|improved|reduced|grew|saved)\s+(?:by\s+)?\d+',
    ]
    achievement_count = sum(len(re.findall(p, text, re.IGNORECASE)) for p in number_patterns)
    score += _tier_score(achievement_count, [(10,5.0),(7,4.0),(5,3.0),(3,2.0),(1,1.0)])

    grammar_penalty = grammar_results.get('penalty_applied', 0.0)
    score += max(0.0, 10.0 - grammar_penalty / 2.0)

    return min(25.0, max(0.0, score))

#4. SKILL VALIDATION SCORE
def _calc_skill_validation_score(validation_results: Dict) -> float:
    return min(15.0, max(0.0, validation_results.get('validation_score', 0.0)))

#5. ATS COMPATIBILITY SCORE
def _calc_ats_compatibility_score(
    text: str,
    location_results: Dict,
    parsed_resume: Dict,
) -> float:

    score = 15.0

    #deduction01
    score -= location_results.get('penalty_applied', 0.0)

    #deduction02
    special_chars = len(re.findall(r'[│┤├┼┴┬╔╗╚╝═║╠╣╦╩╬]', text))
    if special_chars > 20:    score -= 2.0
    elif special_chars > 10:  score -= 1.0

    exp_entries  = [e for e in parsed_resume.get('experience', []) if isinstance(e, dict)]
    edu_entries  = [e for e in parsed_resume.get('education', [])  if isinstance(e, dict)]
    skills_count = len(parsed_resume.get('skills', []))

    exp_desc_len = sum(len(e.get('description', '')) for e in exp_entries)
    edu_desc_len = sum(len((e.get('degree') or '') + (e.get('institution') or '')) for e in edu_entries)  # Handle None to prevent string concatenation errors

    #deduction03
    short_sections = sum([
        bool(exp_entries) and exp_desc_len < 20,
        bool(edu_entries) and edu_desc_len < 20,
        bool(parsed_resume.get('skills')) and skills_count < 2,
    ])
    if short_sections >= 2:    score -= 2.0
    elif short_sections >= 1:  score -= 1.0

    if exp_entries and skills_count > 5:
        score += 1.0

    return min(15.0, max(0.0, score))

#Score aggregation and final interpretation
def calculate_overall_score(
    text: str,
    parsed_resume: Dict,
    skills: List[str],
    keywords: List[str],
    action_verbs: List[str],
    skill_validation_results: Dict,
    grammar_results: Dict,
    location_results: Dict,
    jd_keywords: Optional[List[str]] = None,
    experience_months: int = 0,
) -> Dict:

    # ----------------------------
    # Individual Component Scores
    # ----------------------------

    formatting_score = _calc_formatting_score(parsed_resume, text)
    keywords_score = _calc_keywords_score(keywords, skills, jd_keywords)
    content_score = _calc_content_score(text, action_verbs, grammar_results)
    skill_validation_score = _calc_skill_validation_score(
        skill_validation_results
    )
    ats_compatibility_score = _calc_ats_compatibility_score(
        text,
        location_results,
        parsed_resume,
    )

    # ----------------------------
    # Convert to Percentages
    # ----------------------------

    formatting_pct = (formatting_score / 20.0) * 100
    keyword_pct = (keywords_score / 25.0) * 100
    content_pct = (content_score / 25.0) * 100
    validation_pct = (skill_validation_score / 15.0) * 100
    ats_pct = (ats_compatibility_score / 15.0) * 100

    # ----------------------------
    # ATS Weight Distribution
    # ----------------------------

    score = (
        keyword_pct * 0.35 +
        validation_pct * 0.20 +
        content_pct * 0.20 +
        formatting_pct * 0.10 +
        ats_pct * 0.10
    )

    penalties = {}
    bonuses = {}
        # ----------------------------
    # Grammar Penalty
    # ----------------------------

    grammar_penalty = grammar_results.get("penalty_applied", 0.0)

    if grammar_penalty > 0:
        # NOTE: not subtracted again here — grammar_penalty is already
        # baked into content_score (via _calc_content_score, which does
        # 10.0 - grammar_penalty/2.0). Subtracting it again here was a
        # double-penalty bug. Recorded below for reporting/transparency only.
        penalties["grammar"] = grammar_penalty

    # ----------------------------
    # Location Privacy Penalty
    # ----------------------------

    location_penalty = location_results.get("penalty_applied", 0.0)

    if location_penalty > 0:
        # NOTE: not subtracted again here — location_penalty is already
        # baked into ats_compatibility_score (via _calc_ats_compatibility_score).
        # Subtracting it again here was a double-penalty bug. Recorded below
        # for reporting/transparency only.
        penalties["location_privacy"] = location_penalty

    # ----------------------------
    # Skill Validation Bonus
    # ----------------------------

    validation_ratio = skill_validation_results.get(
        "validation_percentage", 0.0
    )

    if validation_ratio >= 0.90:
        bonuses["excellent_skill_validation"] = 3.0
        score += 3.0

    elif validation_ratio >= 0.75:
        bonuses["good_skill_validation"] = 2.0
        score += 2.0

    elif validation_ratio >= 0.60:
        bonuses["average_skill_validation"] = 1.0
        score += 1.0

    # ----------------------------
    # Perfect Grammar Bonus
    # ----------------------------

    if grammar_results.get("total_errors", 0) == 0:
        bonuses["perfect_grammar"] = 2.0
        score += 2.0

    # ----------------------------
    # Project Bonus
    # ----------------------------

    projects = parsed_resume.get("projects", [])

    if len(projects) >= 3:
        bonuses["excellent_projects"] = 3.0
        score += 3.0

    elif len(projects) == 2:
        bonuses["good_projects"] = 2.0
        score += 2.0

    elif len(projects) == 1:
        bonuses["one_project"] = 1.0
        score += 1.0

    # ----------------------------
    # Experience Bonus
    # ----------------------------

    if experience_months >= 24:
        bonuses["experience"] = 3.0
        score += 3.0

    elif experience_months >= 12:
        bonuses["experience"] = 2.0
        score += 2.0

    elif experience_months >= 6:
        bonuses["experience"] = 1.0
        score += 1.0

    # ----------------------------
    # JD Match Bonus
    # ----------------------------

    if jd_keywords:

        resume_terms = list(
            set(
                [
                    x.lower().strip()
                    for x in (keywords + skills)
                    if x
                ]
            )
        )

        jd_terms = list(
            set(
                [
                    x.lower().strip()
                    for x in jd_keywords
                    if x
                ]
            )
        )

        fuzzy = fuzzy_match_keywords(
            resume_terms,
            jd_terms,
            threshold=75,
        )

        match_pct = (
            len(fuzzy["matched"]) / len(jd_terms)
            if jd_terms
            else 0
        )

        if match_pct >= 0.90:
            bonuses["excellent_jd_match"] = 5.0
            score += 5.0

        elif match_pct >= 0.80:
            bonuses["good_jd_match"] = 4.0
            score += 4.0

        elif match_pct >= 0.70:
            bonuses["average_jd_match"] = 3.0
            score += 3.0

        elif match_pct >= 0.60:
            bonuses["basic_jd_match"] = 2.0
            score += 2.0

        elif match_pct >= 0.50:
            bonuses["minimum_jd_match"] = 1.0
            score += 1.0

    # ----------------------------
    # Normalize Score
    # ----------------------------

    overall_score = round(
        max(0.0, min(score, 100.0)),
        1,
    )

    interpretation = _generate_score_interpretation(
        overall_score
    )

    # ----------------------------
    # Return full result
    # ----------------------------
    # BUG FIX: this function previously computed overall_score/interpretation
    # but never returned anything, so every caller (generate_strengths,
    # generate_critical_issues, generate_improvements) received None and
    # crashed with TypeError: 'NoneType' object is not subscriptable when
    # they tried score_results['formatting_score'] etc. Returning the full
    # breakdown below fixes it.
    return {
        'overall_score':          overall_score,
        'interpretation':         interpretation,
        'formatting_score':       round(formatting_score, 1),
        'keywords_score':         round(keywords_score, 1),
        'content_score':          round(content_score, 1),
        'skill_validation_score': round(skill_validation_score, 1),
        'ats_compatibility_score': round(ats_compatibility_score, 1),
        'component_percentages': {
            'formatting_pct': round(formatting_pct, 1),
            'keyword_pct':    round(keyword_pct, 1),
            'content_pct':    round(content_pct, 1),
            'validation_pct': round(validation_pct, 1),
            'ats_pct':        round(ats_pct, 1),
        },
        'penalties': penalties,
        'bonuses':   bonuses,
    }


#Overall score calculation and interpretation
def generate_strengths(
    score_results: Dict,
    skill_validation_results: Dict,
    grammar_results: Dict,
) -> List[str]:

    strengths = []

    if score_results['formatting_score']       >= 16:
        strengths.append(' Well-structured with clear sections and bullet points')
    if score_results['keywords_score']          >= 20:
        strengths.append(' Strong keyword optimization and skills presence')
    if score_results['content_score']           >= 20:
        strengths.append(' Excellent use of action verbs and quantifiable achievements')
    if score_results['skill_validation_score']  >= 12:
        pct = skill_validation_results.get('validation_percentage', 0) * 100
        strengths.append(f' {pct:.0f}% of skills are validated by projects')
    if score_results['ats_compatibility_score'] >= 13:
        strengths.append(' Excellent ATS compatibility with clean formatting')
    if grammar_results.get('total_errors', 0)   == 0:
        strengths.append(' Error-free grammar and spelling')

    if not strengths:
        strengths.append('Your resume has potential - focus on the recommendations below')
    return strengths


#Critical issues that could cause ATS rejection
def generate_critical_issues(
    score_results: Dict,
    grammar_results: Dict,
    location_results: Dict,
) -> List[str]:
    issues = []

    critical_errors = len(grammar_results.get('critical_errors', []))
    if critical_errors > 0:
        issues.append(f' {critical_errors} critical grammar/spelling error(s) detected')
    if location_results.get('privacy_risk') == 'high':
        issues.append('High privacy risk: Remove detailed location information')
    if score_results['formatting_score']       < 10:
        issues.append(' Poor formatting: Add clear sections and bullet points')
    if score_results['keywords_score']         < 12:
        issues.append(' Insufficient keywords and skills')
    if score_results['skill_validation_score'] < 7:
        issues.append(' Most skills lack supporting evidence in projects')

    return issues


#Actionable improvements to enhance ATS performance
def generate_improvements(
    score_results: Dict,
    skill_validation_results: Dict,
) -> List[str]:
    improvements = []

    if 12 <= score_results['formatting_score']       < 16:
        improvements.append('Add more bullet points and improve section organization')
    if 14 <= score_results['keywords_score']          < 20:
        improvements.append('Include more relevant keywords and technical skills')
    if 14 <= score_results['content_score']           < 20:
        improvements.append('Add more quantifiable achievements and action verbs')
    if 7  <= score_results['skill_validation_score']  < 12:
        unvalidated_count = len(skill_validation_results.get('unvalidated_skills', []))
        improvements.append(f'Validate {unvalidated_count} skill(s) by adding relevant project details')
    if 9  <= score_results['ats_compatibility_score'] < 13:
        improvements.append('Simplify formatting for better ATS compatibility')

    return improvements

#Interpretation of overall score
def _generate_score_interpretation(overall_score: float) -> str:
    if overall_score >= 90:    return 'Excellent! Your resume is highly optimized for ATS systems.'
    elif overall_score >= 80:  return 'Great! Your resume should perform well with most ATS systems.'
    elif overall_score >= 70:  return 'Good! Your resume is ATS-friendly with room for minor improvements.'
    elif overall_score >= 60:  return 'Fair. Your resume needs some improvements to be fully ATS-compatible.'
    elif overall_score >= 50:  return 'Below Average. Significant improvements needed for ATS compatibility.'
    else:                      return 'Poor. Your resume requires major revisions to pass ATS screening.'