from setuptools import setup

def readme():
    with open('README.md') as f:
        return f.read()

setup(name='morningstar_descriptors',
      version='0.1.0',
      description='get financial descriptors from morningstar',
      long_description=readme(),
      classifiers=[
              'Development Status :: 3 - Alpha',
              'License :: GPL3',
              'Programming Language :: Python :: 3.6',
              'Topic :: Computational Finance'],
      url='http://github.com/gykovacs/morningstar_descriptors',
      author='Gyorgy Kovacs',
      author_email='gyuriofkovacs@gmail.com',
      license='GPL3',
      keywords='morningstar descriptor financial-statement',
      packages=['morningstar_descriptors'],
      install_requires=[
              'requests',
              'wikitables',
              'pandas',
              ],
      python_requires='>=27, <4',
      py_modules=['morningstar_descriptors'],
      zip_safe=False)
