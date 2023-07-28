from setuptools import setup, find_packages

setup(
    name='awyes',
    author='Truman Purnell',
    author_email='truman.purnell@gmail.com',
    description='A package for easy setup and management of resources on AWS',
    url='https://github.com/bb-labs/awyes',
    packages=find_packages(),
    install_requires=[
        'boto3',
        'docker',
        'pyyaml',
    ],
    entry_points={'console_scripts': ['awyes=awyes.awyes:main']},
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],
    keywords='aws resources manager setup management',
)
