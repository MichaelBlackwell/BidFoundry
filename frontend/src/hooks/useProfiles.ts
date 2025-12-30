import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { profilesApi, type CreateProfileInput, type UpdateProfileInput } from '../api/profiles';

const PROFILES_KEY = ['profiles'];

export function useProfiles() {
  return useQuery({
    queryKey: PROFILES_KEY,
    queryFn: () => profilesApi.getAll(),
  });
}

export function useProfile(id: string | null) {
  return useQuery({
    queryKey: [...PROFILES_KEY, id],
    queryFn: () => (id ? profilesApi.getById(id) : null),
    enabled: !!id,
  });
}

export function useCreateProfile() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (input: CreateProfileInput) => profilesApi.create(input),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: PROFILES_KEY });
    },
  });
}

export function useUpdateProfile() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (input: UpdateProfileInput) => profilesApi.update(input),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: PROFILES_KEY });
      queryClient.setQueryData([...PROFILES_KEY, data.id], data);
    },
  });
}

export function useDeleteProfile() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => profilesApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: PROFILES_KEY });
    },
  });
}
