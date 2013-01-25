# -*- coding: utf-8 -*-
import unittest2 as unittest

from zope.component import createObject
from zope.component import queryUtility

from plone.dexterity.interfaces import IDexterityFTI

from plone.app.testing import SITE_OWNER_NAME
from plone.app.testing import SITE_OWNER_PASSWORD
from plone.testing.z2 import Browser

from plone.app.textfield.value import RichTextValue

from plone.app.contenttypes.interfaces import IDocument
from Products.CMFPlone.interfaces.constrains import ISelectableConstrainTypes
from plone.app.contenttypes.behaviors import constrains
from Products.CMFCore.utils import getToolByName

from plone.app.contenttypes.testing import (
    PLONE_APP_CONTENTTYPES_INTEGRATION_TESTING,
    PLONE_APP_CONTENTTYPES_FUNCTIONAL_TESTING
)

from plone.app.testing import TEST_USER_ID, setRoles


class DocumentIntegrationTest(unittest.TestCase):

    layer = PLONE_APP_CONTENTTYPES_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.request = self.layer['request']
        self.request['ACTUAL_URL'] = self.portal.absolute_url()
        setRoles(self.portal, TEST_USER_ID, ['Manager'])

        self.portal.invokeFactory('Folder', 'folder')
        self.folder = self.portal['folder']

        self.folder.invokeFactory('Folder', 'inner_folder')
        self.inner_folder = self.folder['inner_folder']

        self.types_tool = getToolByName(self.portal, 'portal_types')
        folder_type = self.types_tool.getTypeInfo(self.folder)
        self.default_types = [t for t in self.types_tool.listTypeInfo() if 
            t.isConstructionAllowed(self.folder) 
            and folder_type.allowType(t.getId())]
        assert len(self.default_types) > 3
        self.types_id_subset = [t.getId() for t in self.default_types][:2]

    def test_behavior_added(self):
        self.assertIn('Products.CMFPlone.interfaces.constrains.ISelectableConstrainTypes',
            self.types_tool.getTypeInfo(self.folder).behaviors)
        self.assertTrue(constrains.IConstrainTypesBehaviorMarker.providedBy(self.folder))
        self.assertTrue(ISelectableConstrainTypes(self.folder))

    def test_constrainTypesModeDefault(self):
        behavior1 = ISelectableConstrainTypes(self.folder)
        behavior2 = ISelectableConstrainTypes(self.inner_folder)
        self.assertEqual(constrains.DISABLED, behavior1.getConstrainTypesMode())
        self.assertEqual(constrains.ACQUIRE, behavior2.getConstrainTypesMode())

    def test_constrainTypesModeValidSet(self):
        behavior = ISelectableConstrainTypes(self.folder)
        behavior.setConstrainTypesMode(constrains.ENABLED)
        self.assertEqual(constrains.ENABLED, behavior.getConstrainTypesMode())

    def test_constrainTypesModeInvalidSet(self):
        behavior = ISelectableConstrainTypes(self.folder)
        self.assertRaises(ValueError, behavior.setConstrainTypesMode, "INVALID")

    def test_canSetConstrainTypesMode(self):
        behavior = ISelectableConstrainTypes(self.folder)
        self.assertEqual(1, behavior.canSetConstrainTypes())

    def test_locallyAllowedTypesDefaultWhenDisabled(self):
        """
        Constrain Mode Disabled.
        We get the default constrains, independent of what our parent folder
        or we ourselves defined
        """
        behavior = ISelectableConstrainTypes(self.inner_folder)
        behavior.setConstrainTypesMode(constrains.DISABLED)
        behavior.setLocallyAllowedTypes([])

        outer_behavior = ISelectableConstrainTypes(self.folder)
        outer_behavior.setConstrainTypesMode(constrains.ENABLED)
        outer_behavior.setLocallyAllowedTypes([])

        types = self.default_types
        type_ids = [t.getId() for t in types]

        self.assertEqual(types, behavior.allowedContentTypes())
        self.assertEqual(type_ids, behavior.getLocallyAllowedTypes())

    def test_locallyAllowedTypesDefaultWhenEnabled(self):
        """
        Constrain Mode enabled
        We get the set constrains, independent of what our parent folder
        defined
        """
        behavior = ISelectableConstrainTypes(self.inner_folder)
        behavior.setConstrainTypesMode(constrains.ENABLED)
        behavior.setLocallyAllowedTypes(self.types_id_subset)

        outer_behavior = ISelectableConstrainTypes(self.folder)
        outer_behavior.setConstrainTypesMode(constrains.ENABLED)
        outer_behavior.setLocallyAllowedTypes([])

        types = [t for t in self.default_types 
            if t.getId() in self.types_id_subset]
        type_ids = self.types_id_subset

        self.assertEqual(types, behavior.allowedContentTypes())
        self.assertEqual(type_ids, behavior.getLocallyAllowedTypes())

    def test_locallyAllowedTypesDefaultWhenAcquired(self):
        """
        Constrain Mode set to ACQUIRE
        Try to acquire the constrains, if that fails, use the defaults
        """
        behavior = ISelectableConstrainTypes(self.inner_folder)
        behavior.setConstrainTypesMode(constrains.ACQUIRE)
        behavior.setLocallyAllowedTypes([])

        outer_behavior = ISelectableConstrainTypes(self.folder)
        outer_behavior.setConstrainTypesMode(constrains.ENABLED)
        outer_behavior.setLocallyAllowedTypes(self.types_id_subset)

        types = self.types_id_subset

        self.assertEqual(types, behavior.getLocallyAllowedTypes())

        outer_behavior.setConstrainTypesMode(constrains.ACQUIRE)

        types = self.default_types
        type_ids = [t.getId() for t in types]

        self.assertEqual(types, behavior.allowedContentTypes())
        self.assertEqual(type_ids, behavior.getLocallyAllowedTypes())

    def test_locallyAllowedTypesInvalidSet(self):
        behavior = ISelectableConstrainTypes(self.folder)
        self.assertRaises(ValueError, 
            behavior.setLocallyAllowedTypes, self.types_id_subset + ['invalid'])

    def test_locallyAllowedTypesInvalidValuesGetFiltered(self):
        behavior = ISelectableConstrainTypes(self.folder)
        behavior.setConstrainTypesMode(constrains.ENABLED)
        self.folder._pac_locally_allowed_types = self.types_id_subset + ['invalid']
        self.assertEqual(self.types_id_subset, behavior.getLocallyAllowedTypes())

    def test_immediatelyAllowedTypesDefaultWhenDisabled(self):
        """
        Constrain Mode Disabled.
        We get the default addables, independent of what our parent folder
        or we ourselves defined
        """
        behavior = ISelectableConstrainTypes(self.inner_folder)
        behavior.setConstrainTypesMode(constrains.DISABLED)
        behavior.setImmediatelyAddableTypes([])

        outer_behavior = ISelectableConstrainTypes(self.folder)
        outer_behavior.setConstrainTypesMode(constrains.ENABLED)
        outer_behavior.setImmediatelyAddableTypes([])

        types = [t.getId() for t in self.default_types]

        self.assertEqual(types, behavior.getImmediatelyAddableTypes())

    def test_immediatelyAllowedTypesDefaultWhenEnabled(self):
        """
        Constrain Mode enabled
        We get the set constrains, independent of what our parent folder
        defined
        """
        behavior = ISelectableConstrainTypes(self.inner_folder)
        behavior.setConstrainTypesMode(constrains.ENABLED)
        behavior.setImmediatelyAddableTypes(self.types_id_subset)

        outer_behavior = ISelectableConstrainTypes(self.folder)
        outer_behavior.setConstrainTypesMode(constrains.ENABLED)
        outer_behavior.setImmediatelyAddableTypes([])

        types = self.types_id_subset

        self.assertEqual(types, behavior.getImmediatelyAddableTypes())

    def test_immediatelyAllowedTypesDefaultWhenAcquired(self):
        """
        Constrain Mode set to ACQUIRE
        Try to acquire the constrains, if that fails, use the defaults
        """
        behavior = ISelectableConstrainTypes(self.inner_folder)
        behavior.setConstrainTypesMode(constrains.ACQUIRE)
        behavior.setImmediatelyAddableTypes([])

        outer_behavior = ISelectableConstrainTypes(self.folder)
        outer_behavior.setConstrainTypesMode(constrains.ENABLED)
        outer_behavior.setImmediatelyAddableTypes(self.types_id_subset)

        types = self.types_id_subset

        self.assertEqual(types, behavior.getImmediatelyAddableTypes())

        outer_behavior.setConstrainTypesMode(constrains.ACQUIRE)

        types = [t.getId() for t in self.default_types]

        self.assertEqual(types, outer_behavior.getImmediatelyAddableTypes())

    def test_immediatelyAllowedTypesInvalidSet(self):
        behavior = ISelectableConstrainTypes(self.folder)
        self.assertRaises(ValueError, 
            behavior.setImmediatelyAddableTypes, self.types_id_subset + ['invalid'])

    def test_immediatelyAllowedTypesInvalidValuesGetFiltered(self):
        behavior = ISelectableConstrainTypes(self.folder)
        behavior.setConstrainTypesMode(constrains.ENABLED)
        self.folder._pac_immediately_addable_types = self.types_id_subset + ['invalid']
        self.assertEqual(self.types_id_subset, behavior.getImmediatelyAddableTypes())

    def test_defaultAddableTypesDefault(self):
        behavior = ISelectableConstrainTypes(self.folder)
        self.assertEqual(self.default_types, behavior.getDefaultAddableTypes())

    def test_allowedContentTypesExit1(self):
        """
        Constrains are disabled, use the portal ones
        """
        behavior = ISelectableConstrainTypes(self.folder)

        types = behavior._getAddableTypesFor(self.portal, self.folder)

        behavior.setConstrainTypesMode(constrains.DISABLED)
        self.assertEquals(types, behavior.allowedContentTypes())

    def test_allowedContentTypesExit2(self):
        """
        Constrains are acquired, parent folder is Plone Site
        """
        behavior = ISelectableConstrainTypes(self.folder)

        types = behavior._getAddableTypesFor(self.portal, self.folder)

        behavior.setConstrainTypesMode(constrains.ACQUIRE)
        self.assertEquals(types, behavior.allowedContentTypes())

    def test_allowedContentTypesExit3(self):
        """
        Constrains are acquired, parent folder is of same type
        """
        outer_behavior = ISelectableConstrainTypes(self.folder)

        assert len(outer_behavior.getLocallyAllowedTypes()) > 2
        outer_behavior.setLocallyAllowedTypes(self.types_id_subset)
        outer_behavior.setConstrainTypesMode(constrains.ENABLED)

        behavior = ISelectableConstrainTypes(self.inner_folder)
        behavior.setConstrainTypesMode(constrains.ACQUIRE)
        self.assertEquals(self.types_id_subset, 
            [x.getId() for x in behavior.allowedContentTypes()])

    def test_allowedContentTypesExit4(self):
        """
        Constrains are enabled
        """
        behavior = ISelectableConstrainTypes(self.folder)

        behavior.setLocallyAllowedTypes(self.types_id_subset)
        behavior.setConstrainTypesMode(constrains.ENABLED)

        self.assertEquals(self.types_id_subset, 
            [x.getId() for x in behavior.allowedContentTypes()])


class FolderConstrainViewFunctionalText(unittest.TestCase):

    layer = PLONE_APP_CONTENTTYPES_FUNCTIONAL_TESTING

    def setUp(self):
        app = self.layer['app']
        self.portal = self.layer['portal']
        self.request = self.layer['request']
        setRoles(self.portal, TEST_USER_ID, ['Manager'])
        self.portal_url = self.portal.absolute_url()
        self.portal.invokeFactory('Folder', id='folder', title='My Folder')
        self.folder = self.portal.folder
        self.folder_url = self.folder.absolute_url()
        import transaction
        transaction.commit()
        self.browser = Browser(app)
        self.browser.handleErrors = False
        self.browser.addHeader(
            'Authorization',
            'Basic %s:%s' % (SITE_OWNER_NAME, SITE_OWNER_PASSWORD,)
        )

    def test_folder_view(self):
        self.browser.open(self.folder_url + '/view')
        self.assertTrue('My Folder' in self.browser.contents)
        self.assertTrue('Restrictions' in self.browser.contents)



def test_suite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
