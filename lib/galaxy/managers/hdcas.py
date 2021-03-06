"""
Manager and Serializer for HDCAs.

HistoryDatasetCollectionAssociations (HDCAs) are datasets contained or created in a
history.
"""

from galaxy import model

from galaxy.managers import base
from galaxy.managers import secured
from galaxy.managers import deletable
from galaxy.managers import taggable
from galaxy.managers import annotatable

from galaxy.managers import hdas

import logging
log = logging.getLogger( __name__ )


# TODO: to DatasetCollectionInstanceManager
class HDCAManager(
        base.ModelManager,
        secured.AccessibleManagerMixin,
        secured.OwnableManagerMixin,
        deletable.PurgableManagerMixin,
        taggable.TaggableManagerMixin,
        annotatable.AnnotatableManagerMixin ):
    """
    Interface/service object for interacting with HDCAs.
    """
    model_class = model.HistoryDatasetCollectionAssociation
    foreign_key_name = 'history_dataset_collection_association'

    tag_assoc = model.HistoryDatasetCollectionTagAssociation
    annotation_assoc = model.HistoryDatasetCollectionAnnotationAssociation

    def __init__( self, app ):
        """
        Set up and initialize other managers needed by hdcas.
        """
        super( HDCAManager, self ).__init__( app )

    # TODO: un-stub


# serializers
# -----------------------------------------------------------------------------
class DCESerializer( base.ModelSerializer ):
    """
    Serializer for DatasetCollectionElements.
    """

    def __init__( self, app ):
        super( DCESerializer, self ).__init__( app )
        self.hda_serializer = hdas.HDASerializer( app )
        self.dc_serializer = DCSerializer( app, dce_serializer=self )

        self.default_view = 'summary'
        self.add_view( 'summary', [
            'id', 'model_class',
            'element_index',
            'element_identifier',
            'element_type',
            'object'
        ])

    def add_serializers( self ):
        super( DCESerializer, self ).add_serializers()
        self.serializers.update({
            'model_class'   : lambda *a, **c: 'DatasetCollectionElement',
            'object'        : self.serialize_object
        })

    def serialize_object( self, item, key, **context ):
        if item.hda:
            return self.hda_serializer.serialize_to_view( item.hda, view='summary', **context )
        if item.child_collection:
            return self.dc_serializer.serialize_to_view( item.child_collection, view='detailed', **context )
        return 'object'


class DCSerializer( base.ModelSerializer ):
    """
    Serializer for DatasetCollections.
    """

    def __init__( self, app, dce_serializer=None ):
        super( DCSerializer, self ).__init__( app )
        self.dce_serializer = dce_serializer or DCESerializer( app )

        self.default_view = 'summary'
        self.add_view( 'summary', [
            'id',
            'create_time',
            'update_time',
            'collection_type',
            'populated',
            'populated_state',
            'populated_state_message',
        ])
        self.add_view( 'detailed', [
            'elements'
        ], include_keys_from='summary' )

    def add_serializers( self ):
        super( DCSerializer, self ).add_serializers()
        self.serializers.update({
            'model_class'   : lambda *a, **c: 'DatasetCollection',
            'elements'      : self.serialize_elements
        })

    def serialize_elements( self, item, key, **context ):
        returned = []
        for element in item.elements:
            serialized = self.dce_serializer.serialize_to_view( element, view='summary', **context )
            returned.append( serialized )
        return returned


class DCASerializer( base.ModelSerializer ):
    """
    Base (abstract) Serializer class for HDCAs and LDCAs.
    """

    def __init__( self, app, dce_serializer=None ):
        super( DCASerializer, self ).__init__( app )
        self.dce_serializer = dce_serializer or DCESerializer( app )

        self.default_view = 'summary'
        self.add_view( 'summary', [
            'id',
            'collection_type',
            'populated',
            'populated_state',
            'populated_state_message',
        ])
        self.add_view( 'detailed', [
            'elements'
        ], include_keys_from='summary' )

    def add_serializers( self ):
        super( DCASerializer, self ).add_serializers()
        # most attributes are (kinda) proxied from DCs - we need a serializer to proxy to
        self.dc_serializer = DCSerializer( self.app )
        # then set the serializers to point to it for those attrs
        collection_keys = [
            'create_time',
            'update_time',
            'collection_type',
            'populated',
            'populated_state',
            'populated_state_message',
            'elements'
        ]
        for key in collection_keys:
            self.serializers[ key ] = self._proxy_to_dataset_collection( key=key )

    def _proxy_to_dataset_collection( self, serializer=None, key=None ):
        # dataset_collection associations are (rough) proxies to datasets - access their serializer using this remapping fn
        # remapping done by either kwarg key: IOW dataset attr key (e.g. populated_state)
        # or by kwarg serializer: a function that's passed in (e.g. elements)
        if key:
            return lambda i, k, **c: self.dc_serializer.serialize( i.collection, [ k ], **c )[ k ]
        if serializer:
            return lambda i, k, **c: serializer( i.collection, key or k, **c )
        raise TypeError( 'kwarg serializer or key needed')


class HDCASerializer(
        DCASerializer,
        taggable.TaggableSerializerMixin,
        annotatable.AnnotatableSerializerMixin ):
    """
    Serializer for HistoryDatasetCollectionAssociations.
    """

    def __init__( self, app ):
        super( HDCASerializer, self ).__init__( app )
        self.hdca_manager = HDCAManager( app )

        self.default_view = 'summary'
        self.add_view( 'summary', [
            'id', 'name',
            'type_id',
            'history_id', 'hid',
            'history_content_type',
            'collection_type',
            'populated',
            'populated_state',
            'populated_state_message',
            'deleted',
            # 'purged',
            'visible',
            'type',
            'url'
        ])
        self.add_view( 'detailed', [
            'elements'
        ], include_keys_from='summary' )

    def add_serializers( self ):
        super( HDCASerializer, self ).add_serializers()
        taggable.TaggableSerializerMixin.add_serializers( self )
        annotatable.AnnotatableSerializerMixin.add_serializers( self )

        self.serializers.update({
            'model_class'               : lambda *a, **c: self.hdca_manager.model_class.__class__.__name__,
            'type'                      : lambda *a, **c: 'collection',
            # part of a history and container
            'history_id'                : self.serialize_id,
            'history_content_type'      : lambda *a, **c: self.hdca_manager.model_class.content_type,
            'type_id'                   : self.serialize_type_id,

            'url'   : lambda i, k, **c: self.url_for( 'history_content_typed',
                                                      history_id=self.app.security.encode_id( i.history_id ),
                                                      id=self.app.security.encode_id( i.id ),
                                                      type=self.hdca_manager.model_class.content_type ),
        })
