from setuptools import setup

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name='clockify_cli',
    version='1.10',
    py_modules=['clockify_cli'],
    description='Clockify.me terminal interface',
    long_description=long_description,
    long_description_content_type="text/markdown",
    author='Benjamin Zachariae',
    url='https://github.com/arcuo/clockify-cli',
    install_requires=[
        'click==7.1.1',
        'certifi==2020.4.5.1',
        'chardet==3.0.4',
        'idna==2.9',
        'requests==2.23.0',
        'urllib3==1.25.9',
        'pytz==2019.3',
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: MIT License",
        "Operating System :: OS Independent",
    ],
    entry_points='''
        [console_scripts]
        clockify=clockify_cli.clockify_cli:main
   ''', 
)
