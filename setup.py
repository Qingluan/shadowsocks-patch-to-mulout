from setuptools import setup, find_packages


setup(name='x-mroy-1050',
    version='0.0.7',
    description=' x-mroy',
    url='https://github.com/Qingluan/.git',
    author='Qing luan',
    author_email='darkhackdevil@gmail.com',
    license='MIT',
    include_package_data=True,
    zip_safe=False,
    packages=find_packages(),
    install_requires=['termcolor'],
    entry_points={
        'console_scripts': [
            'x-sstest=shadowsocks_extentsion.test_route:main',
            'x-sspatch=shadowsocks_extentsion.sspatch:main',
            ]
    },

)
