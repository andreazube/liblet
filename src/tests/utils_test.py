import unittest

from liblet.utils import letstr, Stack, Queue


class UtilsTest(unittest.TestCase):

    def test_str(self):
        self.assertEqual('test', letstr('test'))

    def test_emptyset(self):
        self.assertEqual('{x}', letstr(set()))

    def test_emptyfrozenset(self):
        self.assertEqual('{}', letstr(frozenset()))

    def test_sefofstr(self):
        self.assertEqual('{a, b, c}', letstr({'a', 'b', 'c'}))

    def test_sefofsetofstr(self):
        self.assertEqual(
                '{{a, b, c}, {d, e}}',
                letstr(
                    {frozenset({'a', 'b', 'c'}), frozenset({'d', 'e'})}
                )
            )

    def test_stack(self):
        s = Stack()
        s.push(1)
        s.push(2)
        s.push(3)
        n = len(s)
        out = s.pop()
        actual = '{} {} {}'.format(n, out, s)
        expected = '3 3 Stack(1, 2)'
        self.assertEqual(expected, actual)

    def test_queue(self):
        q = Queue()
        q.enqueue(1)
        q.enqueue(2)
        q.enqueue(3)
        n = len(q)
        out = q.dequeue()
        actual = '{} {} {}'.format(n, out, q)
        expected = '3 1 Queue(2, 3)'
        self.assertEqual(expected, actual)

    def test_bounded_stack(self):
        s = Stack(maxlen = 2)
        s.push(1)
        s.push(2)
        s.push(3)
        n = len(s)
        out = s.pop()
        actual = '{} {} {}'.format(n, out, s)
        expected = '2 3 Stack(2)'
        self.assertEqual(expected, actual)

    def test_bounded_queue(self):
        q = Queue(maxlen = 2)
        q.enqueue(1)
        q.enqueue(2)
        q.enqueue(3)
        n = len(q)
        out = q.dequeue()
        actual = '{} {} {}'.format(n, out, q)
        expected = '2 2 Queue(3)'
        self.assertEqual(expected, actual)


if __name__ == '__main__': unittest.main()