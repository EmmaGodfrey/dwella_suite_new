# Frontend Data Flow

Dwella Suite should keep server data in TanStack Query, not in random page state or template stores.

## Default Chain

```text
Screen / page
  -> domain query or mutation hook
  -> API client
  -> Django REST endpoint
  -> TanStack Query cache
  -> reusable React template components
```

## Folder Pattern

```text
frontend/src/
  Services/
    apiClient.js      # fetch wrapper, auth header, API base URL
    queryClient.js    # TanStack Query defaults
    queryKeys.js      # stable cache keys
    queries.js        # starter shared hooks
  Components/
    ...template components
  Route/
    ...route definitions and guards
```

As features grow, move broad hooks into feature files:

```text
frontend/src/features/properties/
  propertyApi.js
  propertyQueries.js
  PropertyListPage.jsx
  PropertyForm.jsx
```

## Rules

- Use TanStack Query for backend data: lists, detail records, current user, organization context, mutations.
- Use local component state for temporary UI state: modals, active tab, form drafts, selected row.
- Use a tiny client store only for client-only app state: sidebar, theme, selected organization, auth token metadata.
- Do not duplicate server data into Redux/Zustand unless there is a very specific reason.
- Pages should not call `fetch` directly. They should call query/mutation hooks.
- Reusable UI should come from the React Viho template first, then be simplified for Dwella Suite.

## Example

```jsx
function PropertiesPage() {
  const propertiesQuery = usePropertiesQuery({ management_status: "managed" });

  if (propertiesQuery.isLoading) return <Loader />;
  if (propertiesQuery.isError) return <ErrorState message={propertiesQuery.error.message} />;

  return <PropertyTable rows={propertiesQuery.data.results} />;
}
```
