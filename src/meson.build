pkgdatadir = get_option('prefix') / get_option('datadir') / meson.project_name()
moduledir = pkgdatadir / 'trivia_quiz'
gnome = import('gnome')

gnome.compile_resources('trivia-quiz',
  'trivia-quiz.gresource.xml',
  gresource_bundle: true,
  install: true,
  install_dir: pkgdatadir,
)

python = import('python')

conf = configuration_data()
conf.set('PYTHON', python.find_installation('python3').full_path())
conf.set('VERSION', meson.project_version())
conf.set('localedir', get_option('prefix') / get_option('localedir'))
conf.set('pkgdatadir', pkgdatadir)

configure_file(
  input: 'trivia-quiz.in',
  output: 'trivia-quiz',
  configuration: conf,
  install: true,
  install_dir: get_option('bindir'),
  install_mode: 'r-xr--r--'
)

trivia_sources = [
  '__init__.py',
  'main.py',
  'window.py',
  'backend.py',
  'question.py',
]

install_data(trivia_sources, install_dir: moduledir)
