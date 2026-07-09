# frozen_string_literal: true

module Decidim
  module AdminApi
    class CreateComponentType < BaseAdminMutation
      graphql_name "CreateComponent"
      description "Creates a component under a participatory space."
      type Decidim::AdminApi::ComponentType

      argument :attributes, GraphQL::Types::JSON, required: true
      argument :locale, GraphQL::Types::String, required: true
      argument :space_id, GraphQL::Types::ID, required: true
      argument :space_type, GraphQL::Types::String, required: false

      def resolve(space_id:, attributes:, locale:, space_type: nil)
        space = participatory_space(space_id, space_type)
        authorize_admin!(:create, :component, space)

        attrs = component_attributes(attributes, locale)
        manifest = Decidim.find_component_manifest(attrs.fetch(:manifest_name).to_sym)
        raise Decidim::Api::Errors::ValidationError, "Unknown component manifest" unless manifest

        form = component_form(manifest, space, attrs)

        Decidim::Admin::CreateComponent.call(form) do
          on(:ok) { |component| return component.reload }
          on(:invalid) { validation_error!(form) }
        end
      end
    end
  end
end
