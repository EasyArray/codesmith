from setuptools import setup, find_packages

VERSION = '0.0.1' 
DESCRIPTION = 'Platform for Task-Specific Languages built on IPython / Jupyter notebooks'
with open("README.md", "r") as fh:
    LONG_DESCRIPTION = fh.read()

# Setting up
setup(
        name="codesmith", 
        version=VERSION,
        author="Ezra Keshet",
        author_email="ezrakeshet@gmail.com",
        description=DESCRIPTION,
        long_description=LONG_DESCRIPTION,
        packages=find_packages(),
        install_requires=['svgling', 'astor', 'pyparsing'],
        
        keywords=['IPython', 'task-specific languages'],
        classifiers= [
            "Development Status :: 3 - Alpha",
            "Intended Audience :: Education",
            "Programming Language :: Python :: 3",
            "Framework :: IPython",
            "License :: OSI Approved :: MIT License",
            "Intended Audience :: Science/Research",
            "Topic :: Text Processing :: Linguistic",
            "Topic :: Utilities",
            "Framework :: Jupyter",
            "Environment :: Web Environment"
        ]
)