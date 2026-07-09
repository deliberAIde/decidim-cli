# frozen_string_literal: true

module Decidim
  module AdminApi
    class ComponentType < Decidim::Api::Types::BaseObject
      description "A Decidim component returned from admin API mutations."

      field :id, GraphQL::Types::ID, null: false
      field :manifest_name, GraphQL::Types::String, null: false
      field :name, Decidim::Core::TranslatedFieldType, null: false
      field :published_at, Decidim::Core::DateTimeType, null: true
      field :weight, GraphQL::Types::Int, null: false
    end
  end
end
