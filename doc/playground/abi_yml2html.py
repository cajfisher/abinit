#! /usr/bin/env python

import yaml
import re
import argparse
from variables import *

debug = 1

# Path relative from HTML files
js_path = "../"
users_path = "../../users/"

################################################################################
# Definitions

def format_dimensions(dimensions):

  if dimensions is None:
    s = ''
  elif dimensions == "scalar":
    s = ''
  else:
    #s = str(dimensions)
    if isinstance(dimensions,list):
      s = '('
      for dim in dimensions:
        s += str(dim) + ','

      s = s[:-1]
      s += ')'
    else:
      s = str(dimensions)
 
  return s

def doku2html(text):

  def replace_link(mymatch):
    varname = mymatch.group()[2:-2]
    return "<b>"+varname+"</b>"

  p = re.compile("\*\*([a-zA-Z0-9_ */<>]*)\*\*")
  text2 = p.sub(replace_link,text)

  return text2

def format_default(defaultval):

  if defaultval is None:
    s = 'No default'
  else:
    s = "Default is "+str(defaultval)
 
  return s

def make_links(text,cur_varname,variables,characteristics,specials):

  def replace_link(mymatch):
    varname = mymatch.group()[2:-2]
    if varname == cur_varname:
      return "<b>"+cur_varname+"</b>"
    elif varname in variables.keys():
      section = variables[varname]
      return "<a href=\""+section+".html#"+varname+"\">"+varname+"</a>"
    elif varname in characteristics:
      return "<a href=\""+users_path+"abinit_help.html#"+str.replace(varname.lower()," ","_")+"\">"+varname+"</a>"
    elif varname in specials:
      return "<a href=\"specials.html#"+varname+"\">"+varname+"</a>"
    else:
      return "<a href=\"#\">[[FAKE LINK:"+varname+"]]</a>"
    return mymatch.group()

  p=re.compile("\\[\\[([a-zA-Z0-9_ */<>]*)\\]\\]")
  if text is None:
    return ""
  #try:
  new_text=p.sub(replace_link,text)
  #except:
  #  print("Trying to compile :"+str(text))


  return new_text

################################################################################
# Parse the yml file -> variables

file='abinit_vars.yml'

parser = argparse.ArgumentParser(description='Tool for eigenvalue analysis')
parser.add_argument('-f','--file',help='YML file to be read')
args = parser.parse_args()
args_dict = vars(args)
if args_dict['file']:
  file = args_dict['file']

print("Will use "+str(file)+" as input file")

with open(file, 'r') as f:
    variables = yaml.load(f);


# Parse the headers of allvariables and special variables files also replace the JS_PATH.

with open('html_template/temp_allvariables.html') as f:
    header_all = f.read()

with open('html_template/temp_specials.html') as f:
    header_specials = f.read()

header_all = header_all.replace("__JS_PATH__",js_path)

all_contents = dict()
all_vars = dict()

# Create a dictionary that gives the section for each varname

list_all_vars = dict()

for var in variables:
  list_all_vars[var.varname] = var.section

#
cur_specials = []
for (specialkey,specialval) in list_specials:
  cur_specials.append(specialkey)

################################################################################
# Constitute the body of information for all variables, stored for the appropriate section in all_contents[section]

# Initialize the all variable file output
output = ''
output = output + header_all + "<br />\n"
cur_let = 'A'
output = output + "<p>"+cur_let+".&nbsp;\n"

for i, var in enumerate(variables):
  if debug==1 :
    print(var)
  #output = output + "<a href=\""+var.section+".html#"+var.varname+"\">"+var.varname+"</a> : "+var.definition+"<br />\n" 
  while not var.varname.startswith(cur_let.lower()):
    cur_let = chr(ord(cur_let)+1)
    output = output + "<p>"+cur_let+".\n"
  varname = var.varname
  if var.characteristics is not None and '[[INTERNAL_ONLY]]' in var.characteristics:
    varname = '%'+varname
  output = output + "<a href=\""+var.section+".html#"+var.varname+"\">"+varname+"</a>&nbsp;&nbsp;\n" 
  section = var.section
  if section not in all_contents.keys():
    all_contents[section] = "<br><br><br><br><hr>\n"
    all_vars[section] = []

  all_vars[section].append([var.varname,var.definition])

  # Constitute the body of information related to one input variable
  cur_content = ""

  try:
    cur_content += "<br><font id=\"title\"><a name=\""+var.varname+"\">"+var.varname+"</a></font>\n"
    cur_content += "<br><font id=\"definition\">Mnemonics: "+var.definition+"</font>\n"
    if var.characteristics is not None:
      chars = ""
      for chs in var.characteristics:
        chars += chs+", "
      chars = chars[:-2]
      cur_content += "<br><font id=\"characteristic\">Characteristic: "+make_links(chars,var.varname,list_all_vars,list_chars,cur_specials)+"</font>\n"
    else:
      cur_content += "<br><font id=\"characteristic\">Characteristic: </font>\n"
    if var.topic_name is not None:
      cur_content += "<br><font id=\"characteristic\">Mentioned in \"How to\": "+"<a href=\""+var.topic_name+".html\">"+var.topic_name+"</a></font>\n"
    cur_content += "<br><font id=\"vartype\">Variable type: "+var.vartype
    if var.dimensions is not None:
      cur_content += make_links(format_dimensions(var.dimensions),var.varname,list_all_vars,list_chars,cur_specials)
    if var.commentdims is not None and var.commentdims != "":
      cur_content += " (Comment: "+make_links(var.commentdims,var.varname,list_all_vars,list_chars,cur_specials)+")"
    cur_content += "</font>\n" 
    cur_content += "<br><font id=\"default\">"+make_links(format_default(var.defaultval),var.varname,list_all_vars,list_chars,cur_specials)
    if var.commentdefault is not None and var.commentdefault != "":
      cur_content += " (Comment: "+make_links(var.commentdefault,var.varname,list_all_vars,list_chars,cur_specials)+")"
    cur_content += "</font>\n" 
    if var.requires is not None and var.requires != "":
      cur_content += "<br><br><font id=\"requires\">\nOnly relevant if "+doku2html(make_links(var.requires,var.varname,list_all_vars,list_chars,cur_specials))+"\n</font>\n"
    if var.excludes is not None and var.excludes != "":
      cur_content += "<br><br><font id=\"excludes\">\nThe use of this variable forbids the use of "+doku2html(make_links(var.excludes,var.varname,list_all_vars,list_chars,cur_specials))+"\n</font>\n"
    cur_content += "<br><font id=\"text\">\n"
    cur_content += "<p>\n"+doku2html(make_links(var.text,var.varname,list_all_vars,list_chars,cur_specials))+"\n"
    cur_content += "</font>\n\n"
    cur_content += "<br><br><br><br><a href=#top>Go to the top</a>\n"
    cur_content += "<B> | </B><a href=\"allvariables.html#top\">Complete list of input variables</a><hr>\n"
    all_contents[section] = all_contents[section] + cur_content + "\n\n"
  except AttributeError as e:
    print(e)
    print('For variable : ',varname)

################################################################################
# Generate the files that document all the variables.

# For each "normal" section file : generate the header, generate the alphabetical list, write these,
# then complete the content (that was previously gathered), then write the file and close it
for section, content in all_contents.items():
  file_cur = 'html_automatically_generated/'+section+'.html'
  f_cur = open(file_cur,'w')

  with open('html_template/temp_'+section+'.html') as f:
    header_varX = f.read()

  cur_header_varX = header_varX.replace("__JS_PATH__",js_path)
 
  f_cur.write(cur_header_varX)
  cur_let = 'A'
  f_cur.write(" <br>"+cur_let+".\n")
  for varname,defi in all_vars[section]:
    #curlink = "<br /><a href=\"#"+varname+"\">"+varname+"</a> : "+defi+"\n"
    while not varname.startswith(cur_let.lower()):
      cur_let = chr(ord(cur_let)+1)
      f_cur.write(" <br>"+cur_let+".\n")
    curlink = " <a href=\"#"+varname+"\">"+varname+"</a>&nbsp;&nbsp;\n"
    f_cur.write(curlink)
    #f_cur.write("<br /><br />\n")
  f_cur.write("\n")
  content += "<script type=\"text/javascript\" src=\""+js_path+"list_internal_links.js\"> </script>\n\n"
  content += "</body>\n"
  content += "</html>"
  f_cur.write(content)
  f_cur.write("\n")
  f_cur.close()

# Special file : complete the content, then write the file and close it
file_specials = 'html_automatically_generated/specials.html'
f_sp = open(file_specials,'w')
header_specials = header_specials.replace("__JS_PATH__",js_path)
f_sp.write(header_specials)
cur_let = 'A'
cur_content = "<br><br><a href=#top>Go to the top</a><hr>\n"
f_sp.write("<br>"+cur_let+".&nbsp;\n")
for (speckey, specval) in list_specials:
  #curlink = "<br /><a href=\"#"+varname+"\">"+varname+"</a> : "+defi+"\n"
  while not speckey.lower().startswith(cur_let.lower()):
    cur_let = chr(ord(cur_let)+1)
    f_sp.write("<br>"+cur_let+".&nbsp;\n")
  curlink = "<a href=\"#"+speckey+"\">"+speckey+"</a>&nbsp;&nbsp;\n"
  f_sp.write(curlink)

  cur_content += "<br><font id=\"title\"><a name=\""+speckey+"\">"+speckey+"</a></font>\n"
  cur_content += "<br><font id=\"text\">\n"
  cur_content += "<p>\n"+doku2html(make_links(specval,speckey,list_all_vars,list_chars,cur_specials))+"\n"
  cur_content += "</font>"
  cur_content += "<br><br><a href=#top>Go to the top</a><hr>\n"

f_sp.write(cur_content)


cur_content = "\n<script type=\"text/javascript\" src=\""+js_path+"list_internal_links.js\"> </script>\n\n"
cur_content += "</body>\n"
cur_content += "</html>"

f_sp.write(cur_content)
f_sp.close()

# Allvariables file : complete the content, then write the file and close it
output += "<script type=\"text/javascript\" src=\""+js_path+"list_internal_links.js\"> </script>\n\n"
output += "</body>\n"
output += "</html>"

file_html = 'html_automatically_generated/allvariables.html'
f_html = open(file_html,'w')
f_html.write(output)
f_html.close()

################################################################################
# Constitute the body of information for all variables, stored for the appropriate topic_names in all_contents_topics[topic_name]
topic_content = dict()
topic_class_content = dict()
found = dict()
for i, var in enumerate(variables):
  if var.topic_name not in topic_content.keys():
    topic_name = var.topic_name
    topic_class_content[topic_name] = ""
    topic_content[topic_name] = ""
    found[topic_name] = 0

print(topic_class_content)

for (tclasskey, tclassval) in list_topics_class:
  for topic_name, value in topic_class_content.items():
    topic_class_content[topic_name] = "<p>"+tclassval+"<p>"
  for i, var in enumerate(variables):
    if tclasskey==var.topic_class : 
      if debug==1 :
        print(var)
      topic_name = var.topic_name
      found[topic_name] = 1
      varname = var.varname
      if var.characteristics is not None and '[[INTERNAL_ONLY]]' in var.characteristics:
        varname = '%'+varname

      # Constitute the line of information related to one input variable
      topic_class_content[topic_name] += "... <a href=\""+var.section+".html#"+var.varname+"\">"+varname+"</a>   "
      topic_class_content[topic_name] += "["+var.definition+"]<br>\n"

      if debug==1 :
        print(topic_class_content)

  for topic_name, value in found.items():
    if found[topic_name] == 1:
      topic_content[topic_name] = topic_content[topic_name] + topic_class_content[topic_name]
      found[topic_name] = 0

################################################################################
# Generate the "topic" files

# For each "topic" file 
for topic_name, content in topic_content.items():
  file_topic = 'html_automatically_generated/'+topic_name+'.html'
  f_topic = open(file_topic,'w')

  with open('html_template/temp_'+topic_name+'.html') as f:
    header_varX = f.read()

  topic_header_varX = header_varX.replace("__JS_PATH__",js_path)
  topic_header_varX += "<script type=\"text/javascript\" src=\""+js_path+"related_input_variables.js\"> </script>\n\n"

  f_topic.write(topic_header_varX)
  content += "<br>"
  content += "<script type=\"text/javascript\" src=\""+js_path+"list_internal_links.js\"> </script>\n\n"
  content += "</body>\n"
  content += "</html>"
  f_topic.write(content)
  f_topic.write("\n")
  f_topic.close()

################################################################################
# Generate the file with the list of names of "Howto" topic files.

# Parse the yml file -> topics

file='topics.yml'

parser = argparse.ArgumentParser(description='Tool for eigenvalue analysis')
parser.add_argument('-f','--file',help='YML file to be read')
args = parser.parse_args()
args_dict = vars(args)
if args_dict['file']:
  file = args_dict['file']

print("Will use "+str(file)+" as input file")

with open(file, 'r') as f:
    topics = yaml.load(f);

# Parse the header of allvariables and special variables files also replace the JS_PATH.

with open('html_template/temp_alltopics.html') as f:
    header_alltopics = f.read()

header_alltopics = header_alltopics.replace("__JS_PATH__",js_path)

print("header_alltopics: ")
print(header_alltopics)

# Initialize the alltopics file output
toutput = ''
toutput = toutput + header_alltopics + "<br />\n"
cur_let = 'A'
toutput = toutput + "<p>"+cur_let+".&nbsp;\n"

# DEBUG Test the content of topics
# for topic in topics:
#  print("topic: "+topic.topic_name)

print("Will enter loop on topics")
for i, topic in enumerate(topics):
  if debug==1 :
    print("topic: "+topic.topic_name)
    print("cur_let: "+cur_let)
  while not (topic.topic_name.startswith(cur_let.lower()) or topic.topic_name.startswith(cur_let.upper())):
    print("cur_let: "+cur_let)
    cur_let = chr(ord(cur_let)+1)
    toutput = toutput + "<p>"+cur_let+".\n"
  topic_name = topic.topic_name
  toutput = toutput + "<br><a href=\""+ topic_name + ".html\">" + topic_name + "</a> [How to "+topic.howto+"] &nbsp;&nbsp;\n"

# Alltopics file : complete the content, then write the file and close it
toutput += "<script type=\"text/javascript\" src=\""+js_path+"list_internal_links.js\"> </script>\n\n"
toutput += "</body>\n"
toutput += "</html>"

file_html = 'html_automatically_generated/alltopics.html'
f_html = open(file_html,'w')
f_html.write(toutput)
f_html.close()

