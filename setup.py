from setuptools import find_packages, setup

from os import path
top_level_directory = path.abspath(path.dirname(__file__))
with open(path.join(top_level_directory, 'README.md'), encoding='utf-8') as file:
    long_description = file.read()

setup(
    name='nextbox_ui_plugin',
    version='1.0.0',
    url='https://github.com/iDebugAll/nextbox-ui-plugin',
    download_url='https://github.com/iDebugAll/nextbox-ui-plugin/archive/v1.0.0.tar.gz',
    description='Next-Gen topology visualization plugin for Netbox powered by topoSphere SDK.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Igor Korotchenkov',
    author_email='iDebugAll@gmail.com',
    install_requires=[],
    packages=find_packages(),
    license='MIT',
    license_files=('LICENSE', 'LICENSE-topoSphere'),
    include_package_data=True,
    keywords=['netbox', 'netbox-plugin', 'plugin'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
)
