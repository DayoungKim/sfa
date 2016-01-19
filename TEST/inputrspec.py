import sys

class InputRspec:
    rspec_string = None
    dest = 'result.rspec'
    def __init__(self, rspec_string=None, source_file=None, dst_file=None, change_list=[]):
        if rspec_string:
            self.rspec_string = rspec_string
        if source_file:
            self.rspec_string = open(source_file).read()
        if dst_file:
            self.dest = dst_file
        if len(change_list) > 0:
            self.replace(change_list)

    def replace(self, change_list=[]):
        if self.rspec_string == None:
            raise Exception, 'source is None'
        for key, value in change_list:
            self.rspec_string = self.rspec_string.replace(key, value)

    def write(self, dst_file=None):
        print self.rspec_string
        if dst_file:
            self.dest = dst_file
        open(self.dest,'w').write(self.rspec_string)

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print 'usage : python %s source.rspec dest.rspec [ key=value ]' %__file__
        sys.exit()

    args = sys.argv[3:]

    change_list = []
    for arg in args:
        if len(arg.split('='))==2:
            key=arg.split('=')[0]
            value=arg.split('=')[1]
            change_list.append((key, value))

    rspec = InputRspec(source_file=sys.argv[1], dst_file=sys.argv[2], change_list=change_list) 
    rspec.write()
