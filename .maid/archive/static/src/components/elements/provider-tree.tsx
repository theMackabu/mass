type ComposedProvider = Component<Children>;
type FlexibleProvider = Component<NonNullableChildren> | Component<Children>;

type ProviderConfig =
  | [FlexibleProvider]
  | [FlexibleProviderWithProps<Record<string, unknown>>, Record<string, unknown>];
type FlexibleProviderWithProps<TProps extends Record<string, unknown>> =
  | Component<NonNullableChildren & TProps>
  | Component<Children<TProps>>;

export function buildProvidersTree<TProviders extends ReadonlyArray<ProviderConfig>>(
  providers: TProviders,
): ComposedProvider {
  return providers.reduce<ComposedProvider>(
    (AccumulatedProviders, providerConfig) => {
      const [Provider, props = {}] = providerConfig;
      return ({ children }) => (
        <AccumulatedProviders>
          <Provider {...props}>{children}</Provider>
        </AccumulatedProviders>
      );
    },
    ({ children }) => children,
  );
}
