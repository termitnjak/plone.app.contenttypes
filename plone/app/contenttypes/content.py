from zope.interface import implements

from plone.dexterity.content import Container

from plone.app.contenttypes.interfaces import (
    IDocument,
    IEvent,
    IFile,
    IFolder,
    IImage,
    ILink,
    INewsItem
)
#
# All types should be folderish regardless of whether
# you can actually add content by default to them.
#

class Document(Container):
    implements(IDocument)


class Event(Container):
    implements(IEvent)


class File(Container):
    implements(IFile)


class Folder(Container):
    implements(IFolder)


class Image(Container):
    implements(IImage)


class Link(Container):
    implements(ILink)


class NewsItem(Container):
    implements(INewsItem)
