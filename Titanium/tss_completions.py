import sys
import sublime, sublime_plugin
import re
sys.path.append(sublime.packages_path() + '/Titanium/TiDoc/')

import Ti
tss_data = """
"accessibilityHidden" = <boolean>
"backgroundColor"=<color>
"backgroundImage"=<string>
"backgroundPosition"=left | center | right | top | bottom | inherit
"backgroundRepeat"=repeat | repeat-x | repeat-y | no-repeat | inherit
"borderColor"=<color>
"borderWidth"= <size>
"borderRound"= <size>
"bottom"=<size>
"color"=<color>
"font" = {font}
"height"= <size>
"contentHeight"=<size>
"contentWidth"=<size>
"left"=<size>
"right"=<size>
"textAlign"="left" | "right" | "center" | "left"
"top"=<size>
"visible"= <boolean>
"width"=<size>
"zIndex"= <integer> 
"text"=<string>
"""
common = {  
            "Common" : [("StringArray", "['${1:element1}','${2:element2}', '${3:element3}']"),( "Float","${1:0}.${2:0}"), ("true", "true"), ("false","false"), ("Ti.UI.SIZE", "Ti.UI.SIZE"), ("Ti.UI.FILL", "Ti.UI.FILL"),("integer", "${1:0}"), ("L(tag)", "L('${1:tagname}')"), ("L(tag,opt)","L('${1:tagName}', '${2:optionalTagName}')"), ('hexColor','"#${1:FFF}"'), ("rgb()", "rgb(${1:255}, ${2:255}, ${3:255})"), ("rgba()", "rgba(${1:255}, ${2:255}, ${3:255}, ${4:255})"), ("transparent", '"transparent"'), ('aqua', '"aqua"'), ('black', '"black"'), ('blue', '"blue"'), ('brown', '"brown"'), ('cyan', '"cyan"'), ("darkgray", '"darkgray"'), ("fuchsia", '"fuchsia"'), ("gray", '"gray"'), ("green", '"green"'), ("lightgray", '"lightgray"'), ("lime", '"lime"'), ("magenta", '"magenta"'), ("maroon", '"maroon"'), ("navy", '"navy"'), ("olive", '"olive"'), ("orange", '"orange"'), ("pink", '"pink"'), ("purple", '"purple"'), ("red", '"red"'), ("silver", '"silver"'), ("teal", '"teal"'), ("white", '"white"'), ("yellow", '"yellow"'),("Point", "{'x': ${1:0}, 'y' : ${2:0} }")]
            }
def getAll():
    print "--------------------------------------------------------------------------------------------------------"
    s = "("
    checked = {}
    for i in Ti.doc:
      for j in Ti.doc[i]['properties']:
        
        permission = 0
        for k in j:
            if k == "permission":
                permission = 1
        if permission:
                checked[j['filename'].replace("-property", "")] = ""
    for i in checked:
        s += i + "|"
    print s + ")"

def parse_tss_data(data):
    props = {}
    for l in data.splitlines():
        if l == "":
            continue

        names, values = l.split('=')

        allowed_values = []
        for v in values.split('|'):
            v = v.strip()
            if v[0] == '<' and v[-1] == '>':
                key = v[1:-1]
                if key in common:
                    allowed_values += common[key]
            else:
                allowed_values.append(v)

        for e in names.split():
            if e[0] == '"':
                props[e[1:-1]] = sorted(allowed_values)
            else:
                break

    return props
def getViewFile(styleFile):
    m = re.match('(^.*[/])*([^/]+)(.tss)$', styleFile)
    splitPath = m.group(1, 2)
    path = splitPath[0].replace('styles', 'views')
    f = open(path+splitPath[1]+".xml")
    xml = f.read()
    f.close
    return xml

def getSelectors(self, view, prefix, locations):
    props = {}
    viewFile = getViewFile(view.file_name())
    for i in viewFile.splitlines():
        temp = re.match('.*id=(\'|").*', i)
        if temp:
            props["\"#" + i.split("id="+temp.group(1))[1].split(temp.group(1))[0]+"$1\""] =  ["{\n$2\n}"]
        temp = re.match(".*(class *= *(\"|')).*", i)
        if temp:
            props["\"." + i.split(temp.group(1))[1].split(temp.group(2))[0] + "$1\""] = ["{\n$2\n}"]
        if (re.match('.*<[^/].*', i) and not re.match(".*Alloy.*", i)):
            props["\"" + i.split("<")[1].split(" ")[0] + "\""] = ["{\n$2\n}"]
        temp = 0
        temp1 = 0
    return props

def getType(view, selector):
    selectorType= ""
    viewFile = getViewFile(view.file_name())
    if "."  == selector[0]:
        selectorType = "class"
    else: 
        if "#" == selector[0]:
            selectorType = "id" 
        else: 
            selectorType = "element"
    if "element" == selectorType:
        return selector
    else:
        for i in viewFile.splitlines():
            if re.match(".*(" + selectorType + " *= *('|\\\")" + selector[1: ] + ").*", i):
                return  i.split("<")[1].split(" ")[0]
def setProperties(typeView):
    props = {}
    for i in Ti.doc["Titanium.UI."+typeView]['properties']:
        permission = 0
        for j in i:
            if j == "permission":
                permission = 1
        if not permission:
            props[i['name']] = ["$1"]
    return props


class TSSCompletions(sublime_plugin.EventListener):
    props = None
    rex = None

    def on_query_completions(self, view, prefix, locations):
        #getAll()
        self.props = {}
        if not view.match_selector(locations[0], "source.tss - meta.selector.tss"):
            return []

        if not self.props:
            if (view.match_selector(locations[0], "meta.property-list.tss") and not view.match_selector(locations[0], "meta.property-value.tss")):
                #f = open(view.file_name())
                #tss = f.read();
                #f.close()
                f = sublime.Region(0 , locations[0])
                tss = view.substr(f)
                element = ""
                for i in tss.splitlines(): #[0 : locations[0]].splitlines():
                    temp = re.search("(\\\"|')((\\.|#|[A-Z|2|3])[-a-zA-Z0-9_]+) *(\\[.*\\])?(\\\"|') *:", i)
                    if temp:
                        element = temp.group(2)
                self.props = setProperties(getType(view, element))#parse_tss_data(tss_data)
                self.rex = re.compile("([a-zA-Z-]+):\s*$")
            else:
                if not view.match_selector(locations[0], "meta.property-value.tss"):
                    self.props = getSelectors(self, view, prefix, locations)#parse_tss_data(tss_data)
                    self.rex = re.compile("([a-zA-Z-]+):\s*$#\.")
                else:
                    if view.match_selector(locations[0], "meta.property-value.tss"):
                        print sorted(common['Common'])
                        return (sorted(common['Common']), sublime.INHIBIT_WORD_COMPLETIONS)

        l = []
        if (view.match_selector(locations[0], "meta.property-name.tss") ):
            loc = locations[0] - len(prefix)
            line = view.substr(sublime.Region(view.line(loc).begin(), loc))

            m = re.search(self.rex, line)
            if m:
                prop_name = m.group(1)
                if prop_name in self.props:
                    values = self.props[prop_name]

                    add_semi_colon = view.substr(sublime.Region(locations[0], locations[0] + 1)) != ','

                    for v in values:
                        desc = v
                        snippet = v

                        if add_semi_colon:
                            snippet += ","

                        if snippet.find("$1") != -1:
                            desc = desc.replace("$1", "")

                        l.append((desc, snippet))
                    print l
                    return (sorted(l), sublime.INHIBIT_WORD_COMPLETIONS)

            return None
        else:
            add_colon = not view.match_selector(locations[0], "meta.property-name.tss")

            for p in self.props:
                if add_colon:
                    l.append((p, p + ": $1,"))
                else:
                    l.append((p, p))
            print l
            return (sorted(l), sublime.INHIBIT_WORD_COMPLETIONS)
