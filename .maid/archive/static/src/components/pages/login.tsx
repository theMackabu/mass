import { Link } from 'wouter';
import { Button, Flex, TextField, Text, Spinner } from '@radix-ui/themes';

import { useState } from 'react';
import { signIn } from '@/hooks/use-auth';
import { displayError } from '@/utils/common';
import { useForm } from '@tanstack/react-form';

export function Login() {
  const [submitted, setSubmitted] = useState(false);

  const form = useForm({
    defaultValues: {
      identifier: '',
      password: '',
      rememberMe: true,
    },

    onSubmit: async ({ value }) => {
      try {
        setSubmitted(true);
        const result = await signIn.email({ email: value.identifier, ...value });
        if (result.error) displayError(setSubmitted, result.error.message);
      } catch {
        displayError(setSubmitted, 'Unexpected error while signing in.');
      }
    },
  });

  return (
    <div className="w-full md:w-sm">
      <div className="flex items-center space-x-1.5">
        <p className="font-medium text-lg text-foreground dark:text-foreground">Logo Here</p>
      </div>

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
              if (!value) return 'Email is required';
              return undefined;
            },
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
                  borderColor: field.state.meta.errors.length > 0 ? 'red' : undefined,
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
              },
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
                    borderColor: field.state.meta.errors.length > 0 ? 'red' : undefined,
                  }}
                />

                <p className="text-sm text-muted-foreground dark:text-muted-foreground">
                  Forgot your password?{' '}
                  <Link
                    href="/auth/forgot-password"
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
}
