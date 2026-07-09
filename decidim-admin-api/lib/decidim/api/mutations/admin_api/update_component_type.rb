# frozen_string_literal: true

module Decidim
  module AdminApi
    class UpdateComponentType < BaseAdminMutation
      graphql_name "UpdateComponent"
      description "Updates a component."
      type Decidim::AdminApi::ComponentType

      argument :attributes, GraphQL::Types::JSON, required: true
      argument :component_id, GraphQL::Types::ID, required: true
      argument :locale, GraphQL::Types::String, required: true

      def resolve(component_id:, attributes:, locale:)
        record = component(component_id)
        authorize_admin!(:update, :component, record)

        attrs = component_attributes(attributes, locale)
        attrs[:name] ||= record.name
        attrs[:settings] = record.settings.to_h unless attrs.key?(:settings)
        unless attrs.key?(:default_step_settings) || attrs.key?(:step_settings)
          if record.participatory_space.allows_steps?
            attrs[:step_settings] = record.step_settings.transform_values(&:to_h)
          else
            attrs[:default_step_settings] = record.default_step_settings.to_h
          end
        end

        manifest = record.manifest
        form = component_form(manifest, record.participatory_space, attrs.reverse_merge(manifest_name: record.manifest_name))

        Decidim::Admin::UpdateComponent.call(form, record) do
          on(:ok) { return record.reload }
          on(:invalid) { validation_error!(form) }
        end
      end
    end
  end
end
