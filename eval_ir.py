"""\
--------------------------------------------------------------------------------
    USE: python <PROGNAME> (options) keyfile response
    ACTION: computes IR system performance measures, given input files:
        * 'keyfile' - a "gold standard" indicating the documents that 
                      are relevant to each query, and 
        * 'response' - the documents retrieved for each query by the system.
    OPTIONS:
        -h : print this help message
        -n INT : only consider the first INT responses for each query
        -i INT : use INT recall points for interpolated precision (def=10)
        -q : print scores for each individual question (not just global averages)
        -f : print summary scores in \"flat\" mode (i.e. as numbers on single line)
    DATAFORMAT:
        In both input files, each line specifies two integers, in the manner:
         QID  DOCID
        which are numeric identifiers for a query (QID) and a document (DOCID),
        respectively, In the 'response' file, the order of lines is assumed to
        give the "ranking" of documents returned for each query by the system,
        with the 'best' (rank 1) document being listed first, and so on. This
        rank order affects the calculation of the "interpolated precision"
        scores, and is used with the "-n" option to decide which responses are
        retained.
--------------------------------------------------------------------------------
"""

import sys, re
import getopt

class CommandLine:
    def __init__(self):
        opts, args = getopt.getopt(sys.argv[1:],'hi:n:qf')
        opts = dict(opts)

        if '-h' in opts:
            self.printHelp()

        if len(args) == 2:
            self.keyfile = args[0]
            self.responsefile = args[1]
        else:
            print >> sys.stderr, '\n*** ERROR: must specify precisely 2 arg files (key,response) ***'
            self.printHelp()
            
        if '-i' in opts:
            self.interp_points = int(opts['-i'])
        else:
            self.interp_points = 10

        if '-n' in opts:
            self.response_limit = int(opts['-n'])
        else:
            self.response_limit = None

        if '-q' in opts:
            self.query_print = True
        else:
            self.query_print = False

        if '-f' in opts:
            self.print_flat = True
        else:
            self.print_flat = False

    def printHelp(self):
        help = __doc__.replace('<PROGNAME>',sys.argv[0],1)
        print >> sys.stderr, help
        exit()

class Key:
    def __init__(self,config):
        skip = re.compile('^\s*($|#)')
        key = open(config.keyfile,'r')
        self.relevant = {}
        for line in key:
            if skip.search(line): continue
            vals = line.split()
            if len(vals) == 2:
                qid = int(vals[0])
                docid = int(vals[1])
                if qid not in self.relevant:
                    self.relevant[qid] = set()
                self.relevant[qid].add(docid)
            else:
                msg = 'ERROR: bad line in key file:<%s>' % line
                raise Exception(msg)
        key.close()
    
    def isRelevant(self,qid,docid):
        if qid in self.relevant:
            if docid in self.relevant[qid]:
                return True
        return False

    def numRelevant(self,qid):
        if qid in self.relevant:
            return len(self.relevant[qid])
        return 0
    
    def qids(self):
        return set(self.relevant.keys())
     
class Response:
    def __init__(self,config,key):
        seen = {}
        self.retrieved = {}
        self.rel_ranks = {}
        skip = re.compile('^\s*($|#)')
        response = open(config.responsefile,'r')
        for line in response:
            if skip.search(line): continue
            vals = line.split()
            if len(vals) != 2:
                msg = 'ERROR: bad line in key file:<%s>' % line
                raise Exception(msg)
            qid = int(vals[0])
            docid = int(vals[1])
            if qid not in seen:
                seen[qid] = set()
                self.retrieved[qid] = 0
                self.rel_ranks[qid] = []
            if (config.response_limit and self.retrieved[qid] >= config.response_limit):
                # response limit specified and reached, so this response ignored 
                continue
            self.retrieved[qid] += 1
            if key.isRelevant(qid,docid) and docid not in seen[qid]:
                self.rel_ranks[qid].append(self.retrieved[qid])
            # duplicate entries are counted, but only *credited* at first occurrence. 
            seen[qid].add(docid)            
        response.close()

    def getRanks(self,qid):
        if qid in self.rel_ranks:
            return self.rel_ranks[qid]
        return []
    
    def qids(self):
        return set(self.retrieved.keys())

    def numRetrieved(self,qid):
        if qid in self.retrieved:
            return self.retrieved[qid]
        return 0
    
    def numRelevantRetrieved(self,qid):
        if qid in self.rel_ranks:
            return len(self.rel_ranks[qid])
        return 0

class Score:
    def __init__(self,config,key,response):
        self.all_queries = sorted(key.qids() | response.qids())
        self.num_queries = len(self.all_queries)
        self.interp_points = config.interp_points
        self.total_relevant = 0
        self.total_retrieved = 0
        self.total_relevant_retrieved = 0
        self.global_interpolation_points = [0.0] * (self.interp_points + 1)
        
        for qid in self.all_queries:
            
            rel = key.numRelevant(qid)
            ret = response.numRetrieved(qid)
            rel_ret = response.numRelevantRetrieved(qid)
            self.total_relevant  += rel
            self.total_retrieved += ret
            self.total_relevant_retrieved += rel_ret
            
            query_interpolation_points = [0.0] * (self.interp_points + 1)
            ranks = response.getRanks(qid)
            for i in range(len(ranks)):
                prec = (i + 1.0) / ranks[i]
                ipt = int(((i + 1.0) * self.interp_points) / rel)
                if prec > query_interpolation_points[ipt]:
                    query_interpolation_points[ipt] = prec
            for i in range(self.interp_points)[::-1]:
                if query_interpolation_points[i] < query_interpolation_points[i+1]:
                    query_interpolation_points[i] = query_interpolation_points[i+1]
                    
            for i in range(self.interp_points + 1):
                self.global_interpolation_points[i] += query_interpolation_points[i]

            if config.query_print:
                self.print_measure1_query(qid,ret,rel,rel_ret)
                self.print_measure2_query(query_interpolation_points)
                
        for i in range(self.interp_points + 1):
            self.global_interpolation_points[i] /= self.num_queries

    def print_measure1_query(self,qid,ret,rel,rel_ret):
        print >> sys.stderr, (
            "Query ID: %d\n"
            "Total number of documents\n"
            "    Retrieved:       %4d\n"
            "    Relevant:        %4d\n"
            "    Rel_Retr:        %4d\n"
            ) % (qid,ret,rel,rel_ret),
    
    def print_measure1_summary(self,config):
        if self.total_retrieved > 0:
            precision = float(self.total_relevant_retrieved)/self.total_retrieved
        else: 
            precision = 0
        if self.total_relevant > 0: 
            recall = float(self.total_relevant_retrieved)/self.total_relevant
        else:
            recall = 0
        if precision + recall > 0:
            fmeasure = (2 * precision * recall)/(precision + recall)
        else:
            fmeasure = 0.0
        if config.print_flat:
            format = '%d %d %d %d %.2f %.2f %.2f'
        else:
            format = (
            "-------------------------------------------\n"
            "Total number of queries: %d\n"
            "Total number of documents over all queries:\n"
            "    Retrieved:       %4d\n"
            "    Relevant:        %4d\n"
            "    Rel_Retr:        %4d\n"
            "Prec/Rec/F across all queries:\n"
            "    Precision:       %.2f\n"
            "    Recall:          %.2f\n"
            "    F-measure:       %.2f\n"
            )
        print >> sys.stderr, format % (
            self.num_queries,
            self.total_retrieved,
            self.total_relevant,
            self.total_relevant_retrieved,
            precision, recall, fmeasure),

    def print_measure2_query(self,inter_pts):
        print >> sys.stderr, "Interpolated Precision:"
        for i in range(self.interp_points + 1):
            print >> sys.stderr, "    at %.2f      =  %.3f" % (
                (float(i) / self.interp_points),
                inter_pts[i])
        print >> sys.stderr

    def print_measure2_summary(self,config):
        if config.print_flat:
            for i in range(self.interp_points + 1):
                print >> sys.stderr, '%.3f' % self.global_interpolation_points[i],
        else:
            print >> sys.stderr, "Interpolated Precision - Averaged over all queries:"
            for i in range(self.interp_points + 1):
                print >> sys.stderr, "    at %.2f      =  %.3f" % (
                    (float(i) / self.interp_points),
                    self.global_interpolation_points[i])
        #print >> sys.stderr

if __name__ == '__main__':
    config = CommandLine()
    key = Key(config)
    response = Response(config,key)
    scorer = Score(config,key,response)
    scorer.print_measure1_summary(config)
    scorer.print_measure2_summary(config)

