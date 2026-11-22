import re
from typing import Dict, List, Set, Tuple

# Comprehensive Technical Skill Taxonomy
SKILL_TAXONOMY: Dict[str, List[str]] = {
    "programming_languages": [
        "C", "C++", "C#", "Python", "Java", "JavaScript", "TypeScript", "Go", "Golang",
        "Rust", "Ruby", "PHP", "Swift", "Kotlin", "Scala", "R", "SQL", "HTML",
        "CSS", "HTML5", "CSS3", "Bash", "Shell", "PowerShell", "Dart", "Perl",
        "Solidity", "MATLAB", "Assembly", "Lua", "Groovy"
    ],
    "frameworks_and_libraries": [
        "React", "React.js", "React Native", "Next.js", "Vue", "Vue.js", "Angular",
        "Node.js", "Express", "Express.js", "Django", "FastAPI", "Flask", "Spring",
        "Spring Boot", "ASP.NET", ".NET", "Ruby on Rails", "Rails", "Tailwind CSS",
        "Bootstrap", "Redux", "GraphQL", "Svelte", "NestJS", "jQuery", "Laravel",
        "Symfony", "Fastify", "Electron", "PyQt", "Tkinter", "Streamlit"
    ],
    "databases": [
        "PostgreSQL", "MySQL", "MongoDB", "Redis", "SQLite", "Oracle",
        "Microsoft SQL Server", "Cassandra", "DynamoDB", "MariaDB", "Elasticsearch",
        "Neo4j", "Firebase", "Firestore", "Snowflake", "Supabase", "CouchDB"
    ],
    "cloud_and_devops": [
        "AWS", "Amazon Web Services", "Azure", "Microsoft Azure", "Google Cloud",
        "GCP", "Docker", "Kubernetes", "K8s", "Terraform", "Ansible", "Jenkins",
        "Git", "GitHub", "GitLab", "GitHub Actions", "CI/CD", "Nginx", "Apache",
        "Linux", "Ubuntu", "Prometheus", "Grafana", "Helm", "OpenShift", "CircleCI",
        "Visual Studio Code", "VS Code", "VSCode", "Visual Studio", "IntelliJ IDEA",
        "PyCharm", "Postman", "Jira", "Eclipse"
    ],
    "ai_and_machine_learning": [
        "PyTorch", "TensorFlow", "Keras", "Scikit-learn", "Hugging Face", "Transformers",
        "BERT", "LLM", "NLP", "Natural Language Processing", "Computer Vision", "OpenCV",
        "Pandas", "NumPy", "SciPy", "Matplotlib", "Seaborn", "LangChain", "LlamaIndex",
        "XGBoost", "LightGBM", "Deep Learning", "Machine Learning", "Artificial Intelligence"
    ]
}

# Special single-letter or short skills requiring precise contextual matching
CASE_SENSITIVE_SKILLS: Set[str] = {"C", "R", "Go"}

# Canonical display mapping for aliases
SKILL_CANONICAL_NAMES: Dict[str, str] = {
    "react.js": "React",
    "react native": "React Native",
    "vue.js": "Vue",
    "express.js": "Express",
    "golang": "Go",
    "k8s": "Kubernetes",
    "amazon web services": "AWS",
    "microsoft azure": "Azure",
    "google cloud": "GCP",
    "html5": "HTML",
    "css3": "CSS",
    "vs code": "Visual Studio Code",
    "vscode": "Visual Studio Code",
    "visual studio code": "Visual Studio Code",
    "deep learning": "Deep Learning",
    "machine learning": "Machine Learning",
    "artificial intelligence": "AI",
    "natural language processing": "NLP",
}


def _compile_skill_matcher(skill: str) -> Tuple[re.Pattern, bool]:
    """Compile boundary-safe regex pattern for a given skill string."""
    escaped = re.escape(skill)
    is_case_sensitive = skill in CASE_SENSITIVE_SKILLS

    if is_case_sensitive:
        pattern = re.compile(rf'(?<![a-zA-Z0-9#+]){escaped}(?![a-zA-Z0-9#+])')
    else:
        pattern = re.compile(rf'(?<![a-zA-Z0-9#+]){escaped}(?![a-zA-Z0-9#+])', re.IGNORECASE)

    return pattern, is_case_sensitive


# Precompile standard skill patterns
COMPILED_PATTERNS: List[Tuple[str, str, re.Pattern]] = []
for category, skills in SKILL_TAXONOMY.items():
    for skill_name in skills:
        if skill_name == "C":
            # Handled via specialized high-precision context detector
            continue
        pat, _ = _compile_skill_matcher(skill_name)
        COMPILED_PATTERNS.append((category, skill_name, pat))


def detect_c_programming(text: str) -> bool:
    """
    High-precision detector for the 'C' programming language.
    Avoids false positives from single letter 'C' in ordinary text, grades, or initials.
    """
    patterns = [
        # Explicit references
        r'(?i)\bC\s*/\s*C\+\+',
        r'(?i)\bC\s*&\s*C\+\+',
        r'(?i)\bC\s+and\s+C\+\+',
        r'(?i)\bC\s+(?:programming|language)\b',
        r'(?i)\bprogramming\s+in\s+C\b',
        # C in programming / technical skill sections
        r'(?i)(?:languages?|programming|technical\s+skills?|technologies)\s*:[^.\n]*?(?:^|[^\w#+])C(?![a-zA-Z0-9#+])',
        # C preceded by other programming languages in a list
        r'(?:Python|Java|C\+\+|C#|SQL|Assembly|Rust)[,\s/|]+C(?![a-zA-Z0-9#+])',
        # C followed by other programming languages or technical topics
        r'(?:^|[^\w#+])C[,\s/|]+(?:Python|Java|C\+\+|C#|SQL|Data\s+Structures|Linux|Assembly|Rust)\b',
    ]
    return any(re.search(p, text) for p in patterns)


def extract_skills(text: str) -> Dict[str, List[str]]:
    """
    Extract verified technical skills from document text.
    Returns categorized skills and a deduplicated flat list.
    """
    categorized: Dict[str, Set[str]] = {
        "programming_languages": set(),
        "frameworks_and_libraries": set(),
        "databases": set(),
        "cloud_and_devops": set(),
        "ai_and_machine_learning": set(),
    }
    all_skills_set: Set[str] = set()

    # Specialized detector for C programming language
    if detect_c_programming(text):
        categorized["programming_languages"].add("C")
        all_skills_set.add("C")

    for category, skill_name, pattern in COMPILED_PATTERNS:
        if pattern.search(text):
            canonical = SKILL_CANONICAL_NAMES.get(skill_name.lower(), skill_name)
            categorized[category].add(canonical)
            all_skills_set.add(canonical)

    return {
        "programming_languages": sorted(list(categorized["programming_languages"])),
        "frameworks_and_libraries": sorted(list(categorized["frameworks_and_libraries"])),
        "databases": sorted(list(categorized["databases"])),
        "cloud_and_devops": sorted(list(categorized["cloud_and_devops"])),
        "ai_and_machine_learning": sorted(list(categorized["ai_and_machine_learning"])),
        "all_skills": sorted(list(all_skills_set)),
    }
