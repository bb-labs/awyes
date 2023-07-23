from setuptools import setup, find_packages

with open('requirements.txt') as f:
    required_packages = f.read().splitlines()

setup(
    name='awyes',
    version='10.0.0',
    author='Truman Purnell',
    author_email='truman.purnell@gmail.com',
    description='A package for easy setup and management of resources on AWS',
    url='https://github.com/bb-labs/awyes',
    packages=find_packages(exclude=['tests', 'docs']),
    install_requires=required_packages,
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
