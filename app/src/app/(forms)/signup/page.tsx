'use client';

import Link from 'next/link';
import { MassLogo } from '@/units/elements/mass-logo';
import { Button, Flex, TextField, Text, Spinner } from 'summit';

import { toast } from 'sonner';
import { useState } from 'react';
import { useForm } from '@tanstack/react-form';
import { authClient } from '@/service/auth/client';

export default () => {
  const [submitted, setSubmitted] = useState(false);

  const form = useForm({
    defaultValues: {
      email: '',
      username: '',
      password: ''
    },

    onSubmit: async ({ value }) => {
      try {
        setSubmitted(true);

        const result = await authClient.signUp.email({
          name: '',
          theme: 'system',
          email: value.email,
          username: value.username,
          password: value.password
        });

        result.error
          ? toast.error(result.error.message) && setSubmitted(false)
          : (location.href = '/app/projects');
      } catch {
        toast.error('Unexpected error during signup.') && setSubmitted(false);
      }
    }
  });

  return (
    <div className="w-full md:w-sm">
      <MassLogo />

      <h3 className="mt-6 text-lg font-semibold text-foreground dark:text-foreground">
        Sign up for Mass
      </h3>

      <p className="mt-2 text-sm text-muted-foreground dark:text-muted-foreground">
        {'Already have an account? '}
        <Link
          href="/login"
          className="font-medium text-primary hover:text-primary/90 dark:text-primary hover:dark:text-primary/90"
        >
          Sign in
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
        <form.Field name="email">
          {field => (
            <Flex direction="column" gap="2">
              <Flex justify="between">
                <Text
                  htmlFor={field.name}
                  className="text-sm font-medium text-foreground dark:text-foreground"
                >
                  Email
                </Text>
              </Flex>

              <TextField.Root
                required
                id={field.name}
                name={field.name}
                type="email"
                autoComplete="email"
                placeholder="james@bond.com"
                value={field.state.value}
                onBlur={field.handleBlur}
                onChange={e => field.handleChange(e.target.value)}
              />
            </Flex>
          )}
        </form.Field>

        <form.Field name="password">
          {field => (
            <Flex direction="column" gap="2">
              <Flex justify="between">
                <Text
                  htmlFor={field.name}
                  className="text-sm font-medium text-foreground dark:text-foreground"
                >
                  Password
                </Text>
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
              />
            </Flex>
          )}
        </form.Field>

        <form.Field name="username">
          {field => (
            <Flex direction="column" gap="2">
              <Flex justify="between">
                <Text
                  htmlFor={field.name}
                  className="text-sm font-medium text-foreground dark:text-foreground"
                >
                  Username
                </Text>
              </Flex>

              <TextField.Root
                required
                id={field.name}
                name={field.name}
                type="text"
                placeholder="james-bond"
                value={field.state.value}
                onBlur={field.handleBlur}
                onChange={e => field.handleChange(e.target.value)}
              />

              <Text color="gray" size="1">
                Username may only contain alphanumeric characters or single hyphens, and cannot
                begin or end with a hyphen.
              </Text>
            </Flex>
          )}
        </form.Field>

        <form.Subscribe>
          {state => (
            <Button
              type="submit"
              disabled={!state.canSubmit || submitted}
              className="mt-4 w-full py-2 font-medium"
            >
              {state.isSubmitting || submitted ? 'Signing up...' : 'Sign Up'}
              <Spinner loading={state.isSubmitting || submitted} />
            </Button>
          )}
        </form.Subscribe>
      </form>
    </div>
  );
};
