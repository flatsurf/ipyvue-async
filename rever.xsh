try:
  input("Are you sure you are on the master branch which is identical to origin/master? [ENTER]")
except KeyboardInterrupt:
  sys.exit(1)

$PROJECT = 'ipyvue-comm'

$ACTIVITIES = [
    'version_bump',
    'changelog',
    'tag',
    'push_tag',
    'pypi',
    'ghrelease'
]

$VERSION_BUMP_PATTERNS = [
    ('ipyvue_comm/__init__.py', r'__version__ = ', r'__version__ = "$VERSION"'),
    ('ipyvue_comm/__init__.py', r'version_info =', f'version_info = {tuple(int(x) for x in $VERSION.split("."))}'),
    ('js/package.json', r'  "version": ', r'  "version": "$VERSION",'),
    ('setup.py', r'    version=', r'    version="$VERSION",'),
]

$CHANGELOG_FILENAME = 'ChangeLog'
$CHANGELOG_TEMPLATE = 'TEMPLATE.rst'
$CHANGELOG_NEWS = 'news'
$CHANGELOG_CATEGORIES = ('Added', 'Changed', 'Removed', 'Fixed')
$PUSH_TAG_REMOTE = 'git@github.com:saraedum/ipyvue-comm.git'

$PYPI_BUILD_COMMANDS = ['sdist', 'bdist_wheel']

$GITHUB_ORG = 'saraedum'
$GITHUB_REPO = 'ipyvue-comm'
