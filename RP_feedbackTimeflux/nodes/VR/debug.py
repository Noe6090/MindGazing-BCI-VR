from timeflux.core.node import Node

class DebugNode(Node):
    def update(self):
        if self.i.ready():
            print("DATA:", self.i.data)
            print("META:", self.i.meta)
            self.o.data = self.i.data
            self.o.meta = self.i.meta
