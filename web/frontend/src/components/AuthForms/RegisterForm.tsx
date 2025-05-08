import { useState } from 'react';
import { TextInput, PasswordInput, Button, Group, Box, Anchor, Text } from '@mantine/core';
import { useAuth } from '../../context/AuthContext';

interface RegisterFormProps {
  onToggleForm: () => void;
}

const RegisterForm: React.FC<RegisterFormProps> = ({ onToggleForm }) => {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [passwordError, setPasswordError] = useState<string | null>(null);
  const { register, isLoading, error } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Validate passwords match
    if (password !== confirmPassword) {
      setPasswordError('Passwords do not match');
      return;
    }
    
    setPasswordError(null);
    
    try {
      await register(name, email, password);
    } catch (err) {
      // Error is handled by the auth context
    }
  };

  return (
    <Box component="form" onSubmit={handleSubmit}>
      <TextInput
        label="Name"
        placeholder="Your name"
        required
        value={name}
        onChange={(e) => setName(e.target.value)}
        mb="md"
      />
      
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
      
      <PasswordInput
        label="Confirm Password"
        placeholder="Confirm your password"
        required
        value={confirmPassword}
        onChange={(e) => setConfirmPassword(e.target.value)}
        error={passwordError}
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
          Already have an account? Login
        </Anchor>
        
        <Button type="submit" loading={isLoading}>
          Register
        </Button>
      </Group>
    </Box>
  );
};

export default RegisterForm;