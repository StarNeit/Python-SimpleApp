
import re, sys

class ReadDocuments:
    def __init__(self,file):
        self.collection_file = file

    def __iter__(self):
        startdoc = re.compile('<document docid\s*=\s*(\d+)\s*>')
        enddoc = re.compile('</document\s*>')
        readingDoc = False
        with open(self.collection_file) as input_fs:
            for line in input_fs:
                m = startdoc.search(line)
                if m:
                    readingDoc = True
                    doc = Document()
                    doc.docid = int(m.group(1))
                elif enddoc.search(line):
                    readingDoc = False
                    yield doc
                elif readingDoc:
                    doc.lines.append(line)

class ReadIndexFile:
    def __init__(self, file):
        self.collection_file = file

    def ReadDocumentCount(self):
        startdoc = re.compile('<documentcount>')
        enddoc = re.compile('</documentcount>')
        readingDoc = False
        with open(self.collection_file) as input_fs:
            for line in input_fs:
                m = startdoc.search(line)
                if m:
                    readingDoc = True
                elif enddoc.search(line):
                    readingDoc = False
                elif readingDoc:
                    return line
        return 0

    def ReadCollectionIndex(self):
        startdoc = re.compile('<collection>')
        enddoc = re.compile('</collection>')
        readingDoc = False
        index = {}
        with open(self.collection_file) as input_fs:
            for line in input_fs:
                m = startdoc.search(line)
                if m:
                    readingDoc = True
                elif enddoc.search(line):
                    readingDoc = False
                elif readingDoc:
                    tokens = line.split(' ')
                    index[tokens[0]] = (int)(tokens[1].split('\n')[0])
        return index

    def ReadDocumentIndex(self):
        startdoc = re.compile('<document>')
        enddoc = re.compile('</document>')
        readingDoc = False
        index = []
        with open(self.collection_file) as input_fs:
            doc_index = {}
            for line in input_fs:
                m = startdoc.search(line)
                if m:
                    readingDoc = True
                    doc_index = {}
                elif enddoc.search(line):
                    readingDoc = False
                    index.append(doc_index)
                elif readingDoc:
                    tokens = line.split(' ')
                    doc_index[tokens[0].split('\n')[0]] = (int)(tokens[1].split('\n')[0])
        return index

    def ReadQueryIndex(self):
        startdoc = re.compile('<query>')
        enddoc = re.compile('</query>')
        readingDoc = False
        index = []
        with open(self.collection_file) as input_fs:
            doc_index = {}
            for line in input_fs:
                m = startdoc.search(line)
                if m:
                    readingDoc = True
                    doc_index = {}
                elif enddoc.search(line):
                    readingDoc = False
                    index.append(doc_index)
                elif readingDoc:
                    tokens = line.split(' ')
                    doc_index[tokens[0].split('\n')[0]] = (int)(tokens[1].split('\n')[0])
        return index

class Document:
    def __init__(self):
        self.docid = 0
        self.lines = []

    def printDoc(self,out = sys.stdout):
        print >> out, "\n[DOCID: %d]" % self.docid
        for line in self.lines:
            print >> out, line,

