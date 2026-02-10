import os
import re
import shutil
import tempfile
import git
from difflib import SequenceMatcher
import uuid

AI_PATTERNS = [
    r'\bhere are (some|a few|the)\b',
    r'\bin conclusion\b',
    r'\bto summarize\b',
    r'\blet me know if you have any questions?\b',
    r'\bthis means that\b',
    r'\boverall\b',
    r'Certainly!',
    r'Sure, here\'s',
    r'I hope this helps',
]


def get_temp_path():
    """Get Windows-compatible temp path with unique name"""
    temp_dir = tempfile.gettempdir()
    unique_name = f"git_clone_{uuid.uuid4().hex[:8]}"
    return os.path.join(temp_dir, unique_name)


def clone_repo(repo_url):
    """Clone public Git repo to unique temp dir"""
    local_path = get_temp_path()  #  create path in pc

    try:
        print(f"Cloning to: {local_path}")
        repo = git.Repo.clone_from(repo_url, local_path, depth=1)  # copy repo in path
        print("Clone successful!")
        return local_path   # return path
    except git.GitCommandError as e:

        raise e


def cleanup_repo(local_path):
    """Safe cleanup after scan"""
    try:
        if os.path.exists(local_path):
            shutil.rmtree(local_path)
            print(f"Cleaned up: {local_path}")
    except:
        pass


def scan_ai_plag(local_path):
    """Scan Python files for AI patterns and similarity"""
    py_files = []
    file_paths = []

    for root, _, files in os.walk(local_path):
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        code = f.read()
                    if len(code.strip()) > 10:
                        py_files.append(code)
                        file_paths.append(os.path.relpath(filepath, local_path))
                except:
                    continue

    results = {
        'total_files': len(py_files),
        'ai_files': [],
        'plag_matches': [],
        'overall_ai_score': 0,
        'overall_plag_score': 0
    }

    if not py_files:
        return results

    # AI Detection
    regex_hits_total = 0
    for i, code in enumerate(py_files):
        hits = sum(1 for pat in AI_PATTERNS if re.search(pat, code, re.IGNORECASE))
        ai_prob = min(hits / max(len(AI_PATTERNS), 1), 1.0)

        # Perplexity proxy (AI code tends to be more uniform)
        lines = len([l for l in code.split('\n') if l.strip()])
        tokens = len(code.split())
        perplexity_proxy = 1.0 - min(lines / tokens * 0.1 if tokens else 0, 0.8)

        ai_score = (ai_prob + perplexity_proxy) / 2

        results['ai_files'].append({
            'file': file_paths[i],
            'ai_score': round(ai_score, 3),
            'hits': hits,
            'flag': ai_score > 0.6
        })
        regex_hits_total += ai_score

    results['overall_ai_score'] = round(regex_hits_total / len(py_files), 3)

    # Plagiarism (file similarity)
    if len(py_files) > 1:
        max_sim = 0
        for i in range(len(py_files)):
            for j in range(i + 1, len(py_files)):
                sim = SequenceMatcher(None, py_files[i], py_files[j]).ratio()
                if sim > max_sim:
                    max_sim = sim
        results['overall_plag_score'] = round(max_sim, 3)

    return results
