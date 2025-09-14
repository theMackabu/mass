'use client';

import useSWR from 'swr';
import { use } from 'react';
import { toast } from 'sonner';
import { formatRelative } from 'date-fns';
import { useRouter } from 'next/navigation';
import { authClient } from '@/service/auth/client';
import { getProject } from '@/actions/get-project';
import { projectRuntime } from '@/actions/project-runtime';

import { CopyIcon } from '@phosphor-icons/react';
import { Button, Badge, DataList, Flex, Code, IconButton, Skeleton } from 'summit';

export default function Page({ params }: Params<{ id: string }>) {
  const { id } = use(params);
  const { push } = useRouter();
  const { data: project, isLoading, mutate } = useSWR(id, getProject);

  const deleteProject = async () => {
    await authClient.apiKey.delete({ keyId: id });
    push('/app/projects');
  };

  const startProject = async () => {
    await projectRuntime(id, 'online');
    await mutate();
  };

  const stopProject = async () => {
    await projectRuntime(id, 'offline');
    await mutate();
  };

  const copyToClipboard = async () => {
    await navigator.clipboard.writeText(
      `https://mcp.ship.ci/socket?auth=${project?.metadata?.auth}`,
    );

    toast.success('Copied to clipboard');
  };

  return (
    <div className="flex flex-col gap-y-3">
      <h1 className="text-4xl font-semibold tracking-tight">
        <Skeleton loading={isLoading}>{project?.name ?? 'Loading'} </Skeleton>
      </h1>

      <DataList.Root>
        <DataList.Item>
          <DataList.Item>
            <DataList.Label>Resource</DataList.Label>
            <DataList.Value>
              <Skeleton loading={isLoading}>{project?.metadata?.kind ?? 'none'}</Skeleton>
            </DataList.Value>
          </DataList.Item>
          <DataList.Item>
            <DataList.Label>Last used</DataList.Label>
            <DataList.Value>
              <Skeleton loading={isLoading}>
                {project?.lastRequest ? (
                  <p className="first-letter:uppercase">
                    {formatRelative(project.lastRequest, new Date())}
                  </p>
                ) : (
                  'Never used'
                )}
              </Skeleton>
            </DataList.Value>
          </DataList.Item>
          <DataList.Label>Status</DataList.Label>
          <DataList.Value>
            <Skeleton loading={isLoading}>
              <Badge
                variant="soft"
                radius="full"
                color={project?.metadata?.status === 'online' ? 'green' : 'gray'}
              >
                {project?.metadata?.status ?? 'offline'}
              </Badge>
            </Skeleton>
          </DataList.Value>
        </DataList.Item>
        <DataList.Item>
          <DataList.Label>URL</DataList.Label>
          <DataList.Value>
            <Flex align="center" gap="2">
              <Code variant="ghost">https://mcp.ship.ci/socket?auth={project?.metadata?.auth}</Code>
              <IconButton
                size="1"
                aria-label="Copy value"
                color="gray"
                variant="ghost"
                onClick={copyToClipboard}
              >
                <CopyIcon />
              </IconButton>
            </Flex>
          </DataList.Value>
        </DataList.Item>
      </DataList.Root>

      <div className="flex gap-x-2 mt-4">
        {project?.metadata?.status === 'offline' ? (
          <Skeleton loading={isLoading}>
            <Button color="green" onClick={startProject}>
              Start
            </Button>
          </Skeleton>
        ) : (
          <Skeleton loading={isLoading}>
            <Button color="tomato" onClick={stopProject}>
              Stop
            </Button>
          </Skeleton>
        )}

        <Skeleton loading={isLoading}>
          <Button onClick={deleteProject} color="red">
            Delete
          </Button>
        </Skeleton>
      </div>
    </div>
  );
}
