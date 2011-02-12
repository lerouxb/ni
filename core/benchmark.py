import time

class BenchmarkTimer(object):
    def __init__(self):
        self.groups = {}
        self.group_order = []
        self.message = None
        self.ts_start = None

    def start(self, message, log=True):
        if self.ts_start:
            raise Exception("timer already started")
        if not message in self.groups:
            self.group_order.append(message)
            if log:
                print message+'...'
        self.message = message
        self.ts_start = time.time()

    def end(self):
        if not self.ts_start:
            raise Exception("timer not started")
        d = time.time()-self.ts_start
        self.groups.setdefault(self.message, []).append(d)

        self.ts_start = None
        self.message = None

    def get_report(self):
        rows = []
        for message in self.group_order:
            results = self.groups[message]
            results.sort()

            d = {
            'message': message,
            'amount': len(results),
            'min': results[0],
            'max': results[-1],
            'avg': sum(results)/len(results)
            }

            rows.append(d)

        return rows

def format_report(rows):
    lines = []

    # format the cells first
    values = []
    for d in rows:
        d2 = {}
        for k in d:
            if k == 'message':
                d2[k] = d[k]+':'
            elif k == 'amount':
                d2[k] = d[k]
            else:
                d2[k] = "%dms" % (d[k]*1000,)
        values.append(d2)

    field_order = 'message amount min max avg'.split(' ')
    template = "%(message)s %(amount)s %(min)s %(max)s %(avg)s"
    headings = {}
    for k in field_order:
        width = max([len(k)]+[len(str(r[k])) for r in values])+1
        template = template.replace('('+k+')s', '('+k+')-'+str(width)+'s')
        headings[k] = k

    lines.append(template % headings)
    lines.append('-'*len(lines[0]))
    for d in values:
        lines.append(template % d)
    return "\n".join(lines)
