from distutils.core import setup

setup(
    name='minbl',
    packages=[
        'minbl',
        'minbl.blueprints',
        'minbl.reusables',
        'minbl.static'
        'minbl.templates'
    ],
    version="0.1",
    description='A minimalist blog',
    author='Kyuunex',
    author_email='kyuunex@protonmail.ch',
    url='https://github.com/Kyuunex/minbl',
    install_requires=[
        'flask',
        'pyotp',
    ],
)