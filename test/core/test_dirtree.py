import os
import unittest
from nose.tools import *
from ni.core.dirtree import RootDirNode, DirNode, FileNode


def test_rootdirnode():
    node = RootDirNode()
    assert node.path == os.path.sep

def test_dirnode():
    node = DirNode(u'/home/leroux')
    assert node.path == u'/home/leroux/'

def test_filenode():
    node = FileNode(u'/home/leroux/test.txt')
    assert node.path == u'/home/leroux/test.txt'

def test_walk():
    root = RootDirNode()
    root.add(u'/home/leroux/test.txt')
    root.add(u'/home/leroux/projects/ni/hello.py')
    root.add(u'/home/leroux/projects/ni/sub/folder/filename.py')

    paths = []

    def callback(node, parent_path):
        paths.append(node.path)

    root.walk(callback)

    assert len(paths) == 10

def test_collapse():
    root = RootDirNode()
    root.add(u'/home/leroux/test.txt')
    root.add(u'/home/leroux/projects/ni/hello.py')
    root.add(u'/home/leroux/projects/ni/sub/folder/filename.py')

    root.collapse()

    paths = []

    def callback(node, parent_path):
        paths.append(node.path)

    root.walk(callback)

    assert len(paths) == 6

