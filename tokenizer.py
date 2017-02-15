from minutes_scanner import MinutesScanner

scanner = MinutesScanner()

def tokenize(text):
    return scanner.tokenize(text)

if __name__ == '__main__':
    import minutes_db
    from pprint import pprint
    from time import time
    start = time()
    count = 0
    for id in xrange(1, 1001):
        count += 1
        print "id=",id
        text = minutes_db.get_minutes(id)['minutes']
        tokens = scanner.tokenize(text)
        #pprint(tokens)
    end = time()
    total_time = end - start
    print "Parsed %d minutes in %f seconds (avg: %f)" % (count, total_time, float(total_time) / count)
