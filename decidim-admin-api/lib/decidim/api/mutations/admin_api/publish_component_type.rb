# frozen_string_literal: true

module Decidim
  module AdminApi
    class PublishComponentType < BaseAdminMutation
      graphql_name "PublishComponent"
      description "Publishes a component."
      type Decidim::AdminApi::ComponentType

      argument :component_id, GraphQL::Types::ID, required: true

      def resolve(component_id:)
        record = component(component_id)
        authorize_admin!(:publish, :component, record)

        Decidim::Admin::PublishComponent.call(record, current_user) do
          on(:ok) { return record.reload }
          on(:invalid) { raise Decidim::Api::Errors::ValidationError, "Component could not be published" }
        end
      end
    end
  end
end
