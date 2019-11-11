import graphene
from graphene_django import DjangoObjectType

from .models import Tracks, Like
from users.schema import UserType
from graphql import GraphQLError
from django.db.models import Q


class TrackType(DjangoObjectType):
    class Meta:
        model = Tracks


class LikeType(DjangoObjectType):
    class Meta:
        model = Like


class Query(graphene.ObjectType):
    tracks = graphene.List(TrackType, search=graphene.String())
    likes = graphene.List(LikeType)

    def resolve_tracks(self, info, search=None):

        if search:
            filter = (
                Q(title__icontains=search) |
                Q(description__icontains=search) |
                Q(url__icontains=search) |
                Q(posted_by__username__icontains=search)
            )
            return Tracks.objects.filter(filter)
        return Tracks.objects.all()

    def resolve_likes(self, info):
        return Like.objects.all()


class CreateTracks(graphene.Mutation):
    tracks = graphene.Field(TrackType)

    class Arguments:
        title = graphene.String()
        description = graphene.String()
        url = graphene.String()

    def mutate(self, info, title, description, url):
        user = info.context.user

        if user.is_anonymous:
            raise GraphQLError('Log in to add a track')

        tracks = Tracks(title=title, description=description, url=url, posted_by=user)
        tracks.save()
        return CreateTracks(tracks=tracks)


class UpdateTracks(graphene.Mutation):
    tracks = graphene.Field(TrackType)

    class Arguments:
        track_id = graphene.Int(required=True)
        title = graphene.String()
        description = graphene.String()
        url = graphene.String()

    def mutate(self, info, track_id, title, description, url):
        user = info.context.user

        tracks = Tracks.objects.get(id=track_id)
        if tracks.posted_by != user:
            raise GraphQLError('not that user')

        tracks.title = title
        tracks.description = description
        tracks.url = url
        tracks.save()
        return UpdateTracks(tracks=tracks)


class DeleteTrack(graphene.Mutation):
    track_id = graphene.Int()

    class Arguments:
        track_id = graphene.Int(required=True)

    def mutate(self, info, track_id):
        user = info.context.user
        tracks = Tracks.objects.get(id=track_id)

        if tracks.posted_by != user:
            raise GraphQLError('Not that user')

        tracks.delete()

        return DeleteTrack(track_id=track_id)


# class CreateLike(graphene.Mutation):
#     user = graphene.Field(UserType)
#     track = graphene.Field(TrackType)
#
#     class Arguments:
#         track_id = graphene.Int(required=True)
#
#     def mutate(self, info, track_id):
#         user = info.context.user
#
#         if user.is_anonymous:
#             raise GraphQLError('not logged in')
#
#         track = Tracks.objects.get(id=track_id)
#
#         if not track:
#             raise GraphQLError('Track not available')
#
#         Like.objects.create(user=user, track=track)
#
#         return CreateLike(user=user, track=track)


class CreateLike(graphene.Mutation):
    user = graphene.Field(UserType)
    tracks = graphene.Field(TrackType)

    class Arguments:
        track_id = graphene.Int(required=True)

    def mutate(self, info, track_id):
        user = info.context.user

        if user.is_anonymous:
            raise GraphQLError('not logged in')

        tracks = Tracks.objects.get(id=track_id)

        if not tracks:
            raise GraphQLError('not tracks')

        Like.objects.create(user=user, tracks=tracks)

        return CreateLike(user=user, tracks=tracks)


class Mutation(graphene.ObjectType):
    create_tracks = CreateTracks.Field()
    update_tracks = UpdateTracks.Field()
    delete_track = DeleteTrack.Field()
    create_like = CreateLike.Field()

