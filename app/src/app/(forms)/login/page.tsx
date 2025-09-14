'use client';

import Link from 'next/link';
import { MassLogo } from '@/units/elements/mass-logo';
import { Button, Flex, TextField, Text, Spinner } from 'summit';

import { toast } from 'sonner';
import { useState } from 'react';
import { useForm } from '@tanstack/react-form';
import { authClient } from '@/service/auth/client';

const isEmail = (str: string) => {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(str);
};

export default () => {
  const [submitted, setSubmitted] = useState(false);

  const form = useForm({
    defaultValues: {
      identifier: '',
      password: ''
    },

    onSubmit: async ({ value }) => {
      try {
        setSubmitted(true);

        const baseParams = {
          rememberMe: true,
          password: value.password
        };

        const result = isEmail(value.identifier)
          ? await authClient.signIn.email({ ...baseParams, email: value.identifier })
          : await authClient.signIn.username({ ...baseParams, username: value.identifier });

        result.error
          ? toast.error(result.error.message) && setSubmitted(false)
          : (location.href = '/app/projects');
      } catch {
        toast.error('Unexpected error while signing in.') && setSubmitted(false);
      }
    }
  });

  return (
    <div className="w-full md:w-sm">
      <MassLogo />

      <h3 className="mt-6 text-lg font-semibold text-foreground dark:text-foreground">
        Sign in to your account
      </h3>

      <p className="mt-2 text-sm text-muted-foreground dark:text-muted-foreground">
        {"Don't have an account? "}
        <Link
          href="/signup"
          className="font-medium text-primary hover:text-primary/90 dark:text-primary hover:dark:text-primary/90"
        >
          Sign up
        </Link>
      </p>

      <form
        onSubmit={e => {
          e.preventDefault();
          e.stopPropagation();
          form.handleSubmit();
        }}
        className="flex flex-col gap-y-6 mt-6"
      >
        <form.Field
          name="identifier"
          validators={{
            onChange: ({ value }) => {
              if (!value) return 'Username or email is required';
              if (value.length < 3) return 'Must be at least 3 characters';

              if (value.includes('@') && !isEmail(value)) {
                return 'Please enter a valid email address';
              }

              if (!value.includes('@') && !/^[a-zA-Z0-9_.-]+$/.test(value)) {
                return 'Username can only contain letters, numbers, dots, hyphens, and underscores';
              }

              return undefined;
            },
            onBlur: ({ value }) => {
              if (!value) return 'Email or username is required';
              return undefined;
            }
          }}
        >
          {field => (
            <Flex direction="column" gap="2">
              <Flex justify="between">
                <Text
                  htmlFor={field.name}
                  className="text-sm font-medium text-foreground dark:text-foreground"
                >
                  Username or email
                </Text>

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
                placeholder="james@bond.com"
                onChange={e => field.handleChange(e.target.value)}
                style={{
                  borderColor: field.state.meta.errors.length > 0 ? 'red' : undefined
                }}
              />
            </Flex>
          )}
        </form.Field>

        <Flex direction="column" gap="2">
          <form.Field
            name="password"
            validators={{
              onChange: ({ value }) => {
                if (!value) return 'Password is required';
                if (value.length < 6) return 'Password must be at least 6 characters';
                return undefined;
              },
              onBlur: ({ value }) => {
                if (!value) return 'Password is required';
                return undefined;
              }
            }}
          >
            {field => (
              <Flex direction="column" gap="2">
                <Flex justify="between">
                  <Text
                    htmlFor={field.name}
                    className="text-sm font-medium text-foreground dark:text-foreground"
                  >
                    Password
                  </Text>

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
                  type="password"
                  autoComplete="password"
                  placeholder="••••••••••"
                  value={field.state.value}
                  onBlur={field.handleBlur}
                  onChange={e => field.handleChange(e.target.value)}
                  style={{
                    borderColor: field.state.meta.errors.length > 0 ? 'red' : undefined
                  }}
                />

                <p className="text-sm text-muted-foreground dark:text-muted-foreground">
                  Forgot your password?{' '}
                  <Link
                    href="/forgot-password"
                    className="font-medium text-primary hover:text-primary/90 dark:text-primary hover:dark:text-primary/90"
                  >
                    Reset password
                  </Link>
                </p>
              </Flex>
            )}
          </form.Field>
        </Flex>

        <form.Subscribe>
          {state => (
            <Button
              type="submit"
              disabled={!state.canSubmit || submitted}
              className="mt-4 w-full py-2 font-medium"
            >
              {state.isSubmitting || submitted ? 'Signing in...' : 'Sign In'}
              <Spinner loading={state.isSubmitting || submitted} />
            </Button>
          )}
        </form.Subscribe>
      </form>
    </div>
  );
};
