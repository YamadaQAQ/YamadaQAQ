from pypinyin import lazy_pinyin
from pypinyin import Style
from pychai import Erbi
import ahocorasick
import itertools
import time
import sys
import re

def pinyin(word):
    return lazy_pinyin(word)[0]

def suoxie(word):
    return lazy_pinyin(word, style=Style.FIRST_LETTER)[0]

def hanzi(word):
    for c in word:
        if not '\u4e00' <= c <= '\u9fa5':
            return False
    return True

def get_product(words):
    listdata = []
    for word in words:
        tamp = []
        if hanzi(word):
            tamp.append(pinyin(word))
            tamp.append(suoxie(word))
        else:
            tamp.append(word)
        listdata.append(tamp)
    result = []
    for _ in itertools.product(*listdata):
        result.append(list(_))
    return result

class ChaiZi(object):
    def __init__(self):
        self.xiaoqing = Erbi('xiaoqing')
    def run(self):
        self.xiaoqing.run()
        for name_c in self.xiaoqing.charList:
            if name_c in self.xiaoqing.component:
                root, strokeList = self.xiaoqing.component[name_c]
                scheme = [root] + strokeList[-1:] * 4
            else:
                tree = self.xiaoqing.tree[name_c]
                first = tree.first
                second = tree.second
                if second.divisible():
                    R1, SL1 = self.xiaoqing.component[first.veryFirst()]
                    R2, SL2 = self.xiaoqing.component[second.first.veryFirst()]
                    R3, SL3 = self.xiaoqing.component[second.second.veryFirst()]
                    scheme = [R1] + [SL2[0], SL2[-1], SL3[0], SL3[-1]]
                elif first.divisible():
                    R1, SL1 = self.xiaoqing.component[first.first.veryFirst()]
                    R2, SL2 = self.xiaoqing.component[first.second.veryFirst()]
                    R3, SL3 = self.xiaoqing.component[second.veryFirst()]
                    scheme = [R1] + [SL2[0], SL2[-1], SL3[0], SL3[-1]]
                else:
                    R1, SL1 = self.xiaoqing.component[first.name]
                    R2, SL2 = self.xiaoqing.component[second.name]
                    scheme = ([R1] + SL2[:3] + SL2[-1:] * 3)[:5]
            code = ''.join(self.xiaoqing.rootSet[root] for root in scheme)
            self.xiaoqing.encoder[name_c] = code

class copyRegex(object):
    def __init__(self, f_name):
        self.f_name = f_name
        self.regex_dict = {} 

    def makeregex(self):
        chai = ChaiZi()
        chai.run()
        with open(self.f_name, "r", encoding="utf-8") as f:
            for ban_word in f.readlines():
                isFirst = True
                pat = ""
                for char in ban_word:
                    if char == '\n' or char.isdigit():
                        break
                    elif char.encode("utf-8").isalpha():
                        if isFirst:
                            isFirst = False
                        else:
                            pat += "[^a-zA-Z]*"
                        pat += "(?:" + char + ")"
                    else:
                        if isFirst:
                            isFirst = False
                        else:
                            pat += "[^\\u4e00-\\u9fa5]*"
                        if char in chai.xiaoqing.tree.keys():
                            zi = chai.xiaoqing.tree[char]
                            if len(zi.first.name) >= 1 and len(zi.second.name) >= 1:
                                pat += "(?:{}|{}|{}|{}{})".format(char, pinyin(char), suoxie(char), zi.first.name[0], zi.second.name[0])
                            else:
                                pat += "(?:{}|{}|{})".format(char, pinyin(char), suoxie(char))
                        else:
                            pat += "(?:{}|{}|{})".format(char, pinyin(char), suoxie(char))
                self.regex_dict[ban_word.strip()] = pat

class AhocorasickCopy:
    def __init__(self, userdata):
        self.userdata = userdata
        self.actre = ahocorasick.Automaton() 

    def addKEYwords(self):
        for idx, key in enumerate(self.userdata):
            self.actre.add_word(key, (idx, key))
        self.actre.make_automaton() 

    def matchresult(self, sentence):
        result = [] #保存答案
        #end_index:匹配结果在sentence中的末尾索引
        #insert_order:匹配结果在AC机中的索引
        for end_index, (insert_order, original_value) in self.actre.iter(sentence):
            strat_index = end_index - len(original_value) + 1
            #print((strat_index, end_index + 1), (insert_order, original_value))
            #result.append([strat_index, end_index])
            result.append(original_value)
        return result

class BlackList(object):
    def __init__(self, f_name):
        self.f_name = f_name 
        self.newword = [] 
        self.newblacklist = {} 

    def makedict(self, regex):
        with open(self.f_name, "r", encoding="utf-8") as f:
            for line in f.readlines():
                for key, val in regex.items():
                    it = re.findall(val, line, re.I)
                    for result in it:
                        self.newblacklist[result] = key
                        self.newword.append(result)
                    if key.encode("utf-8").isalpha():
                        continue
                    mp = {}
                    line = list(line)
                    for i in range(len(line)):
                        CUR = lazy_pinyin(line[i])[0]
                        KEY = lazy_pinyin(key)
                        if CUR in KEY:
                            to = key[KEY.index(CUR)]
                            mp[i] = line[i]
                            line[i] = to
                    line = ''.join(line)
                    it = re.findall(val, line, re.I)
                    for result in it:
                        pos = line.index(result)
                        for i in range(len(result)):
                            if pos + i in mp.keys():
                                result = result.replace(result[i], mp[pos + i])
                        self.newblacklist[result] = key
                        self.newword.append(result)
            self.newword = list(set(self.newword))

def IOput(f_name):
    try:
        f = open(f_name, "r")
    except IOError:
        exit(0)
    else:
        f.close()

class Copycat(object):
    def __init__(self, f_blacklist, f_org, f_ans) -> object:
        self.f_blacklist = f_blacklist
        self.f_org = f_org
        self.f_ans = f_ans

    def run(self):
        IOput(self.f_blacklist)
        IOput(self.f_org)
        copyre = copyRegex(self.f_blacklist)
        copyre.makeregex()
        copydict = BlackList(self.f_org)
        copydict.makedict(copyre.regex_dict)
        ac = AhocorasickCopy(copydict.newword)
        ac.addKEYwords()
        tot = 0
        result = []
        with open(self.f_org, "r", encoding="utf-8") as f:
            for index, line in enumerate(f.readlines()):
                tamp_result = ac.matchresult(line.strip())
                for it in tamp_result:
                    result.append("Line{}: <{}> {}\n".format(index + 1, copydict.newblacklist[it], it))
                    tot = tot + 1
        with open(self.f_ans, "w", encoding="utf-8") as f:
            f.write("Total: {}\n".format(tot))
        with open(self.f_ans, "a", encoding="utf-8") as f:
            f.writelines(result)

if __name__ == "__main__":
    st = time.time()
    if len(sys.argv) == 1:
        f_words = "words.txt"
        f_org = "org.txt"
        f_ans = "ans.txt"
    elif len(sys.argv) == 4:
        f_words = sys.argv[1]
        f_org = sys.argv[2]
        f_ans = sys.argv[3]
    else:
        exit(0)
    aqua = Copycat(f_words, f_org, f_ans)
    aqua.run()
    exit(0)
