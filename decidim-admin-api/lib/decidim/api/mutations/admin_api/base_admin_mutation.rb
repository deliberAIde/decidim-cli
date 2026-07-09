# frozen_string_literal: true

module Decidim
  module AdminApi
    class BaseAdminMutation < Decidim::Api::Types::BaseMutation
      required_scopes "api:read", "admin:read", "admin:write"

      private

      def authorize_admin!(action, subject, object)
        context_hash = context.to_h.merge(
          current_user:,
          current_organization:,
          current_participatory_space: object.is_a?(Decidim::Participable) ? object : nil,
          current_component: object.is_a?(Decidim::Component) ? object : nil
        ).compact

        return true if current_user.present? && allowed_to?(action, subject, object, context_hash)

        raise Decidim::Api::Errors::MutationNotAuthorizedError, I18n.t("decidim.api.errors.unauthorized_mutation")
      end

      def attributes_hash(attributes)
        attributes.to_h.transform_keys { |key| key.to_s.underscore.to_sym }
      end

      def wrap_translatable_attributes(attributes, locale, keys)
        keys.each do |key|
          next unless attributes.key?(key)

          value = attributes[key]
          attributes[key] = if value.is_a?(Hash)
                              value.transform_keys(&:to_s)
                            else
                              { locale => value }
                            end
        end

        attributes
      end

      def process_attributes(attributes, locale, defaults: true)
        attrs = attributes_hash(attributes)
        wrap_translatable_attributes(
          attrs,
          locale,
          %i[
            title subtitle description short_description developer_group local_area
            meta_scope participatory_scope participatory_structure target
          ]
        )

        if defaults
          attrs[:subtitle] ||= attrs[:title]
          attrs[:short_description] ||= attrs[:description] || attrs[:title]
          attrs[:description] ||= attrs[:short_description] || attrs[:title]
          attrs[:weight] ||= 0
          attrs[:access_mode] ||= "open"
          attrs[:has_members] = false unless attrs.key?(:has_members)
          attrs[:promoted] = false unless attrs.key?(:promoted)
          attrs[:related_process_ids] ||= []
        end

        attrs
      end

      def phase_attributes(attributes, locale)
        attrs = attributes_hash(attributes)
        wrap_translatable_attributes(attrs, locale, %i[title description])
        attrs
      end

      def component_attributes(attributes, locale)
        attrs = attributes_hash(attributes)
        wrap_translatable_attributes(attrs, locale, %i[name])
        attrs[:weight] ||= 0
        attrs
      end

      def participatory_process(process_id)
        scope = Decidim::ParticipatoryProcess.where(organization: current_organization)
        scope = scope.with_deleted if scope.respond_to?(:with_deleted)
        scope.find_by(id: process_id) || scope.find_by!(slug: process_id)
      end

      def process_phase(process, phase_id)
        process.steps.find(phase_id)
      end

      def component(component_id)
        Decidim::Component.find(component_id).tap do |record|
          raise ActiveRecord::RecordNotFound unless record.organization == current_organization
        end
      end

      def participatory_space(space_id, space_type = nil)
        manifests = Decidim.participatory_space_manifests
        manifests = manifests.select { |manifest| [manifest.name.to_s, manifest.model_class_name].include?(space_type.to_s) } if space_type.present?

        manifests.each do |manifest|
          klass = manifest.model_class_name.constantize
          scope = klass.where(organization: current_organization)
          found = scope.find_by(id: space_id)
          found ||= scope.find_by(slug: space_id) if klass.column_names.include?("slug")
          return found if found
        end

        raise ActiveRecord::RecordNotFound
      end

      def component_form(manifest, space, attrs)
        settings = ->(name, data) { Decidim::Component.build_settings(manifest, name, data || {}, current_organization) }

        params = {
          manifest:,
          participatory_space: space,
          name: attrs.fetch(:name),
          weight: attrs[:weight],
          settings: settings.call(:global, attrs[:settings])
        }

        if attrs[:default_step_settings]
          params[:default_step_settings] = settings.call(:step, attrs[:default_step_settings])
        else
          params[:step_settings] = (attrs[:step_settings] || {}).transform_values { |value| settings.call(:step, value) }
        end

        form(manifest.component_form_class).from_params(params, current_participatory_space: space)
      end

      def validation_error!(form)
        raise Decidim::Api::Errors::AttributeValidationError, form.errors
      end
    end
  end
end
