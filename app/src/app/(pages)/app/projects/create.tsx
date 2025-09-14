'use client';

import { toast } from 'sonner';
import { useState } from 'react';
import { useForm } from '@tanstack/react-form';
import { authClient } from '@/service/auth/client';
import { useRouter } from 'next/navigation';

import { Dialog, Select, Spinner, Button, Flex, Text, TextField } from 'summit';

type Kind = 'script' | 'website' | 'database' | 'blank' | string;
type DialogProps = Children<{ title?: string; selected: Kind }>;

export function CreateDialog({ title, selected, children }: DialogProps) {
  const { refresh } = useRouter();
  const [open, setOpen] = useState(false);

  const form = useForm({
    defaultValues: {
      name: '',
      kind: selected
    },

    onSubmit: async ({ value }) => {
      await authClient.apiKey.create({
        name: value.name,
        prefix: 'mass',
        metadata: { kind: value.kind, status: 'offline' }
      });

      setOpen(false);
      refresh();

      toast.success('Created project');
    }
  });

  return (
    <Dialog.Root open={open} onOpenChange={setOpen}>
      <Dialog.Trigger>
        {children ?? (
          <button className="text-sm font-medium text-emerald-600 hover:text-emerald-500 dark:text-emerald-400 dark:hover:text-emerald-300 cursor-pointer outline-none">
            {title}
            <span aria-hidden="true"> &rarr;</span>
          </button>
        )}
      </Dialog.Trigger>

      <Dialog.Content maxWidth="450px">
        <Dialog.Title>Create a new project</Dialog.Title>
        <Dialog.Description>This will create a new project and mcp server</Dialog.Description>

        <form
          onSubmit={e => {
            e.preventDefault();
            e.stopPropagation();
            form.handleSubmit();
          }}
          className="flex flex-col gap-y-6 mt-6"
        >
          <form.Field
            name="name"
            validators={{
              onChange: ({ value }) => {
                if (!value) return 'Project name is required';
                if (value.length < 3) return 'Must be at least 3 characters';
                return undefined;
              }
            }}
          >
            {field => (
              <Flex direction="column" gap="1">
                <Text
                  htmlFor={field.name}
                  className="text-sm font-medium text-foreground dark:text-foreground"
                >
                  Project name
                </Text>

                <Flex justify="between">
                  {field.state.meta.errors.length > 0 && (
                    <Text color="red" size="1">
                      {field.state.meta.errors[0]}
                    </Text>
                  )}
                </Flex>

                <TextField.Root
                  required
                  id={field.name}
                  name={field.name}
                  type="text"
                  value={field.state.value}
                  onBlur={field.handleBlur}
                  placeholder="Stardust"
                  onChange={e => field.handleChange(e.target.value)}
                  style={{
                    borderColor: field.state.meta.errors.length > 0 ? 'red' : undefined
                  }}
                />
              </Flex>
            )}
          </form.Field>

          <form.Field name="kind">
            {field => (
              <Flex direction="column" gap="1">
                <Text
                  htmlFor={field.name}
                  className="text-sm font-medium text-foreground dark:text-foreground"
                >
                  Service
                </Text>

                <Select.Root
                  name={field.name}
                  value={field.state.value}
                  onValueChange={value => field.handleChange(value)}
                >
                  <Select.Trigger />
                  <Select.Content>
                    <Select.Group>
                      <Select.Item value="script">Nebula</Select.Item>
                      <Select.Item value="website">Page</Select.Item>
                      <Select.Item value="database">Database</Select.Item>
                      <Select.Item value="blank">Empty project</Select.Item>
                    </Select.Group>
                  </Select.Content>
                </Select.Root>
              </Flex>
            )}
          </form.Field>

          <Flex gap="3" mt="4" justify="end">
            <Dialog.Close>
              <Button variant="soft" color="gray">
                Cancel
              </Button>
            </Dialog.Close>
            <form.Subscribe>
              {state => (
                <Button
                  type="submit"
                  disabled={!state.canSubmit}
                  className="mt-4 w-full py-2 font-medium"
                >
                  {state.isSubmitting ? 'Creating Project...' : 'Create Project'}
                  <Spinner loading={state.isSubmitting} />
                </Button>
              )}
            </form.Subscribe>
          </Flex>
        </form>
      </Dialog.Content>
    </Dialog.Root>
  );
}
