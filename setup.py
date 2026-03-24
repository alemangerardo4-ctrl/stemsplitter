from setuptools import setup
APP=['stemsplitter.py']
OPTIONS={'argv_emulation':False,'packages':['rumps'],'plist':{'CFBundleName':'StemSplitter','CFBundleDisplayName':'StemSplitter','CFBundleIdentifier':'design.publicworks.stemsplitter','CFBundleVersion':'1.0.0','LSUIElement':True,'NSHighResolutionCapable':True}}
setup(app=APP,options={'py2app':OPTIONS},setup_requires=['py2app'])
