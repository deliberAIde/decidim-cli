# frozen_string_literal: true

module Decidim
  module AdminApi
    module MutationExtensions
      def self.included(type)
        type.field :create_participatory_process, Decidim::AdminApi::CreateParticipatoryProcessType, null: false
        type.field :update_participatory_process, Decidim::AdminApi::UpdateParticipatoryProcessType, null: false
        type.field :publish_participatory_process, Decidim::AdminApi::PublishParticipatoryProcessType, null: false
        type.field :unpublish_participatory_process, Decidim::AdminApi::UnpublishParticipatoryProcessType, null: false
        type.field :create_process_phase, Decidim::AdminApi::CreateProcessPhaseType, null: false
        type.field :update_process_phase, Decidim::AdminApi::UpdateProcessPhaseType, null: false
        type.field :activate_process_phase, Decidim::AdminApi::ActivateProcessPhaseType, null: false
        type.field :create_component, Decidim::AdminApi::CreateComponentType, null: false
        type.field :update_component, Decidim::AdminApi::UpdateComponentType, null: false
        type.field :publish_component, Decidim::AdminApi::PublishComponentType, null: false
        type.field :unpublish_component, Decidim::AdminApi::UnpublishComponentType, null: false
      end
    end
  end
end
