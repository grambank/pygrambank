from setuptools import setup, find_packages


setup(
    name='pygrambank',
    version='2.0.0',
    author='Robert Forkel',
    author_email='robert_:forkel@eva.mpg.de',
    description='A python library to curate Grambank data',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    keywords='',
    license='Apache 2.0',
    url='https://github.com/grambank/pygrambank',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    include_package_data=True,
    zip_safe=False,
    entry_points={
        'console_scripts': [
            'grambank=pygrambank.__main__:main',
        ],
    },
    platforms='any',
    python_requires='>=3.6',
    install_requires=[
        'clldutils>=3.6',
        'cldfcatalog',
        'csvw>=1.10',
        'pycldf>=1.6.2',
        'xlrd',
        'openpyxl==2.4.8',
        'pyglottolog>=2.0',
        'tqdm',
        'beautifulsoup4>=4.9.1',
        'ftfy',
        'html5lib',
    ],
    extras_require={
        'dev': ['flake8', 'wheel', 'twine'],
        'test': [
            'pytest>=5.4',
            'pytest-mock',
            'pytest-cov',
            'coverage>=4.2',
        ],
    },
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy'
    ],
)
