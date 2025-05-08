import { useState } from 'react';
import { TextInput, PasswordInput, Button, Group, Box, Anchor, Text } from '@mantine/core';
import { useAuth } from '../../context/AuthContext';

interface LoginFormProps {
  onToggleForm: () => void;
}

const LoginForm: React.FC<LoginFormProps> = ({ onToggleForm }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const { login, isLoading, error } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    try {
      await login(email, password);
    } catch (err) {
      // Error is handled by the auth context
    }
  };

  return (
    <Box component="form" onSubmit={handleSubmit}>
      <TextInput
        label="Email"
        placeholder="your@email.com"
        required
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        mb="md"
      />
      
      <PasswordInput
        label="Password"
        placeholder="Your password"
        required
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        mb="md"
      />
      
      {error && (
        <Text c="red" size="sm" mb="md">
          {error}
        </Text>
      )}
      
      <Group justify="space-between" mt="xl">
        <Anchor
          component="button"
          type="button"
          c="dimmed"
          onClick={onToggleForm}
          size="xs"
        >
          Don't have an account? Register
        </Anchor>
        
        <Button type="submit" loading={isLoading}>
          Login
        </Button>
      </Group>
    </Box>
  );
};

export default LoginForm;