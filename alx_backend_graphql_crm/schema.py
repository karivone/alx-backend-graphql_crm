# alx_backend_graphql_crm/schema.py
import graphene
from crm.schema import Query as CRMQuery, Mutation as CRMMutation

class Query(graphene.ObjectType):
    hello = graphene.String(default_value="Hello, GraphQL!")

schema = graphene.Schema(query=Query)
