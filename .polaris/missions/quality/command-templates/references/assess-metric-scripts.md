# Assessment Metric Collection Scripts

Run each sub-section ONE AT A TIME, sequentially. Do NOT fire multiple sub-sections in parallel. `git grep` returns exit code 1 when it finds no matches (normal) -- parallel execution risks cascading cancellation if any one fails.

## a) Scale and Structure

```
python -c "
import subprocess, collections
try:
    files = subprocess.run(['git','ls-files'], capture_output=True, text=True, timeout=30, check=False).stdout.splitlines()
    print(f'Total tracked files: {len(files)}')
except Exception as e:
    files = []
    print(f'Warning: could not list files: {e}')
print()
try:
    dirs = set()
    for p in files:
        if '/' in p:
            dirs.add('/'.join(p.split('/')[:3]))
    print('Directory tree (top 3 levels):')
    for d in sorted(dirs)[:200]:
        print(f'  {d}')
except Exception as e:
    print(f'Warning: could not build directory tree: {e}')
print()
try:
    exts = collections.Counter(f.rsplit('.',1)[-1] for f in files if '.' in f)
    print('File count by extension:')
    for ext, count in exts.most_common(30):
        print(f'{count:6d} .{ext}')
except Exception as e:
    print(f'Warning: could not count extensions: {e}')
"
```

## b) Lines of Code

If `cloc` available: `cloc . --exclude-dir=node_modules,.venv,vendor,dist,build --quiet`

Otherwise:
```
python -c "import subprocess; files=subprocess.check_output(['git','ls-files','*.py','*.ts','*.js','*.go','*.rs','*.java','*.cs']).decode().splitlines(); total=sum(len(open(f,errors='ignore').readlines()) for f in files if __import__('os.path',fromlist=['exists']).exists(f)); print(f'Total: {total} lines across {len(files)} files')"
```

## c) Dependency Manifests

Search for: `package.json`, `requirements.txt`, `pyproject.toml`, `Cargo.toml`, `go.mod`, `pom.xml`, `*.csproj`, `Gemfile`

## d) Config Files at Root

Check for: `.editorconfig`, `.prettierrc`, `.eslintrc`, `tsconfig.json`, `Dockerfile`, `docker-compose.yml`, `Makefile`, CI configs

---

Record total file count to determine scan depth:
- **Small** (<1,000 files): Read most files directly
- **Medium** (1,000-50,000): Grep patterns + 5-10% sampling
- **Large** (50,000+): Grep patterns only + 1-2% sampling

---

## e) Tech Debt Markers

```
python -c "
import subprocess, collections
markers = ['TODO', 'FIXME', 'HACK', 'XXX', 'WORKAROUND']
globs = ['*.py', '*.ts', '*.js', '*.go', '*.rs', '*.java', '*.cs']
counts = collections.Counter()
for marker in markers:
    try:
        r = subprocess.run(
            ['git', 'grep', '-c', marker, '--'] + globs,
            capture_output=True, text=True, timeout=30, check=False)
        if r.returncode == 0 and r.stdout.strip():
            for line in r.stdout.strip().splitlines():
                parts = line.rsplit(':', 1)
                if len(parts) == 2:
                    counts[parts[0]] += int(parts[1])
    except Exception as e:
        print(f'Warning: skipped {marker}: {e}')
if counts:
    print('Top 15 files by tech debt markers:')
    for filepath, count in counts.most_common(15):
        print(f'  {count:4d} {filepath}')
    print(f'Total: {sum(counts.values())} markers across {len(counts)} files')
else:
    print('No tech debt markers found.')
"
```

## f) Security - Hardcoded Secrets

```
python -c "
import subprocess
scans = [
    ('password assignments', ['password\\s*='], ['*.py','*.ts','*.js','*.yaml','*.yml','*.json',':!*test*',':!*.example']),
    ('api/secret keys', ['api_key\\s*=', 'secret_key\\s*=', 'AWS_SECRET', 'PRIVATE.KEY'], [':!*test*']),
]
for label, patterns, globs in scans:
    print(f'--- {label} ---')
    found = False
    for pat in patterns:
        try:
            r = subprocess.run(
                ['git', 'grep', '-n', pat, '--'] + globs,
                capture_output=True, text=True, timeout=30, check=False)
            if r.returncode == 0 and r.stdout.strip():
                found = True
                print(r.stdout.strip())
        except Exception as e:
            print(f'Warning: skipped pattern {pat}: {e}')
    if not found:
        print('  (no matches)')
    print()
"
```

## g) Security - Injection Risks

```
python -c "
import subprocess
scans = [
    ('SQL injection (f-strings/format)', ['f\\\".*SELECT', 'f\\\".*INSERT', '\\.format.*SELECT'], ['*.py','*.ts','*.js',':!*test*']),
    ('eval/exec/shell injection', ['\\beval\\b', '\\bexec\\b', 'shell=True', 'os\\.system'], ['*.py','*.ts','*.js',':!*test*']),
]
for label, patterns, globs in scans:
    print(f'--- {label} ---')
    found = False
    for pat in patterns:
        try:
            r = subprocess.run(
                ['git', 'grep', '-n', pat, '--'] + globs,
                capture_output=True, text=True, timeout=30, check=False)
            if r.returncode == 0 and r.stdout.strip():
                found = True
                print(r.stdout.strip())
        except Exception as e:
            print(f'Warning: skipped pattern {pat}: {e}')
    if not found:
        print('  (no matches)')
    print()
"
```

## h) Largest Source Files (Complexity Hotspots)

```
python -c "
import subprocess, os
try:
    r = subprocess.run(
        ['git','ls-files','*.py','*.ts','*.js','*.go','*.rs','*.java','*.cs'],
        capture_output=True, text=True, timeout=30, check=False)
    files = r.stdout.splitlines() if r.returncode == 0 else []
except Exception as e:
    print(f'Warning: could not list files: {e}')
    files = []
sizes = []
for f in files:
    try:
        if os.path.exists(f):
            sizes.append((sum(1 for _ in open(f, errors='ignore')), f))
    except Exception:
        pass
if sizes:
    print('Top 20 largest source files:')
    for count, name in sorted(sizes, reverse=True)[:20]:
        print(f'{count:8d} {name}')
else:
    print('No source files found.')
"
```

## i) CI/CD and Docker

Check for: `.github/workflows/`, `.gitlab-ci.yml`, `azure-pipelines.yml`, `Jenkinsfile`, `Dockerfile`, `docker-compose.*`, Helm charts, Terraform files
