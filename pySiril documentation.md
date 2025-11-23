Siril Logo Siril
About(Current)
News(Current)
Docs(Current)
FAQ(Current)
Tutorials(Current)
Forum(Current)
Downloads(Current)
Shop(Current)
🔍 Search(Current)
Donate (Current)  Dogecoin
Languages
Language Icon Translations 
Automating with pySiril
By Cissou8
pySiril is a Python package extending scripting capabilities, present natively in Siril. It is intended for users already familiar with scripts looking for an alternative to using complex shell or bat (on Windows).

With pySiril, you can:

write conditions and loops (if, else, for…)
easily write your own functions
get values returned by some of Siril functions such as stat, bg, cdg, bgnoise…
This library works for the 3 main OS, Linux, Windows and MacOS.

Installation
Modules
Processing example with command wrapper
Processing example with Execute
Using Addons
Functions returning values
Apply a single-image command to a sequence
Installation 
Download the latest version from https://gitlab.com/free-astro/pysiril/-/releases

Uninstall any previous version with:

python -m pip uninstall pysiril
Install the new whl with:
python -m pip install pysiril-0.0.7-py3-none-any.whl
You can also build the package from the latest sources available at https://gitlab.com/free-astro/pysiril

Modules 
pySiril contains 3 modules:

Siril: the main module that will start Siril, start the named pipes and get you going.
Wrapper: the wrapper to all the commands you would type in Siril Command Line or in a script (*.ssf file)
Addons: a convenience class packed with handy stuff to manipulate files, renumber, copy them, read or write seq files.
An example of first use could be something like:

from pysiril.siril import Siril
from pysiril.wrapper import Wrapper
from pysiril.addons import Addons

app=Siril()                                 # Starts pySiril
cmd=Wrapper(app)                            # Starts the command wrapper
                             
help(Siril)                                 # Get help on Siril functions
help(Wrapper)                               # Get help on all Wrapper functions
help(Addons)                                # Get help on all Addons functions

cmd.help()                                  # Lists of all commands
cmd.help('bgnoise')                         # Get help for bgnoise command

del app
Processing example with command wrapper 
The example below shows how to:

Define blocks of commands
Start pySiril, Siril and the command wrapper
Set some preferences
Prepare masterbias, masterflat and masterdark
Preprocess lights with masterflat and masterdark, register and stack.
Closing Siril and exit properly
This processing workflow is similar to the standard Siril script, OSC_Preprocessing.

import sys
import os

from pysiril.siril   import *
from pysiril.wrapper import *

# ==============================================================================
# EXAMPLE OSC_Processing with functions wrapper
# ==============================================================================

#1. defining command blocks for creating masters and processing lights
def master_bias(bias_dir, process_dir):
    cmd.cd(bias_dir )
    cmd.convert( 'bias', out=process_dir, fitseq=True )
    cmd.cd( process_dir )
    cmd.stack( 'bias', type='rej', sigma_low=3, sigma_high=3, norm='no')
    
def master_flat(flat_dir, process_dir):
    cmd.cd(flat_dir )
    cmd.convert( 'flat', out=process_dir, fitseq=True )
    cmd.cd( process_dir )
    cmd.preprocess( 'flat', bias='bias_stacked' )
    cmd.stack( 'pp_flat', type='rej', sigma_low=3, sigma_high=3, norm='mul')
    
def master_dark(dark_dir, process_dir):
    cmd.cd(dark_dir )
    cmd.convert( 'dark', out=process_dir, fitseq=True )
    cmd.cd( process_dir )
    cmd.stack( 'dark', type='rej', sigma_low=3, sigma_high=3, norm='no')
    
def light(light_dir, process_dir):
    cmd.cd(light_dir)
    cmd.convert( 'light', out=process_dir, fitseq=True )
    cmd.cd( process_dir )
    cmd.preprocess('light', dark='dark_stacked', flat='pp_flat_stacked', cfa=True, equalize_cfa=True, debayer=True )
    cmd.register('pp_light')
    cmd.stack('r_pp_light', type='rej', sigma_low=3, sigma_high=3, norm='addscale', output_norm=True, out='../result')
    cmd.close()
    
# ============================================================================== 
# 2. Starting pySiril
app=Siril()       
workdir  = "D:/_TraitAstro/20-SiriL/work/TestSiril"

try:
    cmd=Wrapper(app)    #2. its wrapper
    app.Open()          #2. ...and finally Siril

    #3. Set preferences
    process_dir = '../process'
    cmd.set16bits()
    cmd.setext('fit')

    #4. Prepare master frames
    master_bias(workdir+ '/biases' ,process_dir)
    master_flat(workdir+ '/flats'  ,process_dir)
    master_dark(workdir+ '/darks'  ,process_dir)

    #5. Calibrate the light frames, register and stack them
    light(workdir+ '/lights' ,process_dir)
    
except Exception as e :
    print("\n**** ERROR *** " +  str(e) + "\n" )    

#6. Closing Siril and deleting Siril instance
app.Close()
del app
Of course, you could use Siril script to do the exact same thing. But now imagine you have not shot flats for some reason (cannot be a good one though, there’s no good reason not to shoot flats!). With small modifications to the code above, you could:

test to check if the flats folder contains any file or is present,
adapt the script to skip masterflat preparation,
adapt light processing to skip light calibration with flat.
You would need to do the following.

First modify light() function to accept a kwarg to indicate if flats are present:

def light(light_dir, process_dir,hasflats=True):
    cmd.cd(light_dir)
    cmd.convert( 'light', out=process_dir, fitseq=True )
    cmd.cd( process_dir )
    if hasflats:
        cmd.preprocess( 'light', dark='dark_stacked', flat='pp_flat_stacked', cfa=True, equalize_cfa=True, debayer=True )
    else:
        cmd.preprocess( 'light', dark='dark_stacked', cfa=True, debayer=True )
    cmd.register('pp_light')
    cmd.stack('r_pp_light', type='rej', sigma_low=3, sigma_high=3, norm='addscale', output_norm=True, out='../result')
    cmd.close()
Then modify the main script to check for presence of flats and adapt the processing workflow accordingly.

    #4. Prepare master frames
    flatsdir=workdir+ '/flats'
    hasflats=True
    if not(os.path.isdir(flatsdir)) or (len(os.listdir(flatsdir) == 0): # flats folder does not contain any file or none is present in workdir
        hasflats=False

    if hasflats:
        master_bias(workdir+ '/biases' ,process_dir)
        master_flat(workdir+ '/flats'  ,process_dir)
    
    master_dark(workdir+ '/darks'  ,process_dir)  

    #5. Calibrate the light frames, register and stack them
    light(workdir+ '/lights' ,process_dir,hasflats)
This is just an example, you could do same for darks of course, make all the folder names modular, make it a module with I/O, passing the working directory name etc…

Processing example with Execute 
This code does the same as the example above except it uses extensively the Execute method of Siril class. Execute(‘some command’) works exactly like you typing ‘some command’ in Siril command line.

import sys
import os

from pysiril.siril   import *

# ==============================================================================
# EXAMPLE OSC_Processing with Execute function without wrapper functions
# ==============================================================================

def master_bias(bias_dir, process_dir):
    app.Execute("cd " + bias_dir )
    app.Execute("convert bias -out=" + process_dir + " -fitseq" )
    app.Execute("cd " + process_dir )
    app.Execute("stack bias rej 3 3  -nonorm")
    
def master_flat(flat_dir, process_dir):
    app.Execute("cd " + flat_dir + "\n"
                "convert flat -out=" + process_dir + " -fitseq"   + "\n"
                "cd " + process_dir  + "\n"
                "preprocess flat  -bias=bias_stacked"  + "\n"
                "stack  pp_flat rej  3 3 -norm=mul")
    
def master_dark(dark_dir, process_dir):
    app.Execute(""" cd %s
                    convert dark -out=%s -fitseq
                    cd %s
                    stack dark rej 3 3 -nonorm """ % (dark_dir,process_dir,process_dir) )
    
def light(light_dir, process_dir):
    app.Execute("cd " + light_dir)
    app.Execute("convert light -out=" + process_dir + " -fitseq"  )
    app.Execute("cd " + process_dir )
    app.Execute("preprocess light -dark=dark_stacked -flat=pp_flat_stacked -cfa -equalize-cfa -debayer" )
    app.Execute("register pp_light")
    app.Execute("stack r_pp_light rej 3 3 -norm=addscale -output_norm -out=../result")
    app.Execute("close")
    
# ==============================================================================
workdir     = "/home/barch/siril/work/TestSiril"
try:
    app.Open(  )
    process_dir = '../process'
    app.Execute("set16bits")
    app.Execute("setext fit")
    master_bias(workdir+ '/biases' ,process_dir)
    master_flat(workdir+ '/flats'  ,process_dir)
    master_dark(workdir+ '/darks'  ,process_dir)
    light(workdir+ '/lights' ,process_dir)
except Exception as e :
    print("\n**** ERROR *** " +  str(e) + "\n" )    
    
app.Close( )
del app
Whether you choose to use Execute or wrapper functions is up to you. You know the 2 main ways of controlling Siril with Python.

Using Addons 
The example below shows how to use some of the functions of the Addons class.

import sys
import os

from pysiril.siril   import *
from pysiril.wrapper import *
from pysiril.addons  import *

# ==============================================================================
# Example of addons functions 
# ==============================================================================
app=Siril()
try:
    cmd=Wrapper(app)
    fct=Addons(app)
    
    
    # Create a seqfile
    
    workdir     = "D:/_TraitAstro/20-SiriL/work/TestSiril"
    processdir  = workdir + "/" + "xxxx"
    
    fct.CleanFolder(processdir,ext_list=[ ".cr2",".seq"])
    
    fct.MkDirs(processdir)
    
    NbImage= fct.GetNbFiles(workdir+ '/lights/*.CR2')
    print( "CR2 number:",NbImage)
    
    number=fct.NumberImages(workdir+ '/lights/*.CR2',processdir,"offsets",start=10,bOverwrite=True)
    
    if number == NbImage  :
        fct.CreateSeqFile(processdir+"/toto.seq", number )
    else:
        print("error of images number:",number, "<>",NbImage)
        
except Exception as e :
    print("\n**** ERROR *** " +  str(e) + "\n" )    
    
app.Close()
del app
Functions returning values 
The example below shows how to use functions returning values. It takes as input a *.seq file and writes a csv with values returned by stat command. Note: this example is now obsolete thanks to the seqstat command added in Siril 0.99.8. Nonetheless, it can give you ideas on how to make use of these functions.

import os,sys
import re
import glob
from pysiril.siril import Siril
from pysiril.wrapper import Wrapper
from distutils.util import strtobool
import pandas as pd

       
def Run(inputfilename):

    folder,filename=os.path.split(inputfilename)
    fileroot,_=os.path.splitext(filename)
    os.chdir(folder)

    with open(inputfilename) as f:
        lines = list(line for line in (l.strip() for l in f) if line)

    img=[]
    for i,l in enumerate(lines):
        if l.startswith('S'):
            specline=l.split()
            lenseq=int(specline[3])
            
        if l.startswith('I'):
            tl=l.split()
            img.append(int(tl[1]))

    for ff in glob.iglob(fileroot+'*.f*'):
        _,fitext=os.path.splitext(ff)
        if not(fitext=='.seq'):
            break


    app=Siril(bStable=False)
    app.Open()
    cmd=Wrapper(app)


    res=[]
    for i in range(lenseq):
        fitfile='{0:s}{1:05d}{2:s}'.format(fileroot,img[i],fitext)
        cmd.load(fitfile)
        _,stats=cmd.stat()
        for j in range(len(stats)):
            stats[j]['file']=fitfile
            stats[j]['image#']=img[i]
            res.append(stats[j])
    app.Close()
    del app

    data=pd.DataFrame.from_dict(res)
    data.set_index(['file','image#','layer'],inplace=True)
    data.reset_index(inplace=True)
    data.to_csv(fileroot+'stats.csv',index=False)


if __name__ == "__main__":
    args=[]
    kwargs={}
    for a in sys.argv[1:]:
        if '=' in a:
            f,v=a.split('=')
            kwargs[f]=v
        else:
            args.append(a)
    Run(*tuple(args),**kwargs)
To run it:

copy/paste this code in your favorite editor
save it as seqstat.py
in a shell, type:
python seqstat.py "C:\Users\myusername\Pictures\astro\myseqfile_.seq"
This will save myseqfile_stats.csv in the same folder.

Apply a single-image command to a sequence 
This last example is the python equivalent of the shell scripts shown there . It uses all the notions detailed above. Just copy the code below and save to a file named genseqscript.py.

# Usage
#######
# genseqscript.py command seqname [prefix ext]
# Examples:
###########
#
# Apply a median filter to all images from C:\MyImages\r_pp_light_.seq with "fit" extension and save them with "med_" prefix
# python genseqscript.py "fmedian 5 1" "C:\MyImages\r_pp_light_.seq" med_ fit
#
# Apply a 90 deg rotation w/o crop to all images from pp_light_.seq located in current folder
# python genseqscript.py "rotate 90 -nocrop" pp_light_ rot90_


# User settings
# command: the command to be applied to each image of the sequence. Enclosed in double quotes if there is more than one word
# seqname: name of the sequence, can be a full path or just a sequence namein the current directory (w or w/o .seq extension). Enclosed in double quotes if there are spaces in the path
# prefix: (optional) the prefix to be preprended to the processed file names, def: ""
# ext: (optional) chosen FITS extension, def: fits (can also be fit or fts)
import os,sys
from pysiril.siril import Siril
from pysiril.wrapper import Wrapper
from pysiril.addons import Addons

def Run(command,seqname,prefix='',ext='fits'):

    print('Command to be run: {0:s}'.format(command))
    print('prefix: {0:s}'.format(prefix))
    print('FITS extension: {0:s}'.format(ext))

    if os.path.isabs(seqname):
        currdir,seqname=os.path.split(seqname)
    else:
        currdir=os.getcwd()

    seqname,seqext=os.path.splitext(seqname)
    if len(seqext)==0:
        seqext='.seq'

    print('Working directory: {0:s}'.format(currdir))
    print('Sequence to be processed: {0:s}{1:s}'.format(seqname,seqext))

    if not(os.path.isfile(os.path.join(currdir,seqname+seqext))):
        print('The specified sequence does not exist - aborting')
        sys.exit()

    print('Starting PySiril')
    app = Siril(R'C:\Program Files\SiriL\bin\siril-cli.exe')
    AO = Addons(app)
    cmd = Wrapper(app)

    print('Starting Siril')
    try:
        app.Open()
        seqfile = AO.GetSeqFile(os.path.join(currdir,seqname+seqext))
        app.Execute('setext {:s}'.format(ext))
        app.Execute('cd "{:s}"'.format(currdir))
        for im in seqfile['images']:
            currframenb=im['filenum']
            currframe='{0:s}{1:05d}.{2:s}'.format(seqname,currframenb,ext)
            if not(os.path.isfile(os.path.join(currdir,currframe))):
                print('First file {0:s} does not exist... check if the .seq file is valid or the selected FITS extension ("{1:s}" defined here) matches your files - aborting'.format(currframe,ext))
                sys.exit()
            print('processing file: {0:s}'.format(currframe))
            savename=prefix+currframe
            cmd.load(currframe)
            app.Execute(command)
            cmd.save(savename)
        app.Close()
        del app
    except Exception as e :
        print("\n**** ERROR *** " +  str(e) + "\n" )


if __name__ == "__main__":
    args=[]
    kwargs={}
    for a in sys.argv[1:]:
        if '=' in a:
            f,v=a.split('=',1)
            kwargs[f]=v
        else:
            args.append(a)
    Run(*tuple(args),**kwargs)
Follow us:

   
© Copyright 2025 Siril

PIXLS.US ♡ Siril