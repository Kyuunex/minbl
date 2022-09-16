from distutils.core import setup

setup(
    name='minbl',
    packages=[
        'minbl',
        'minbl.blueprints',
        'minbl.classes',
        'minbl.reusables'
    ],
    include_package_data=True,
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
