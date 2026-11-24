import { describe, it, expect } from 'vitest'
import { z } from 'zod'

describe('Authentication Form Validation Schemas', () => {
  const loginSchema = z.object({
    email: z.string().min(1, 'Email is required').email('Enter a valid email address'),
    password: z.string().min(8, 'Password must be at least 8 characters'),
  })

  const registerSchema = z
    .object({
      email: z.string().min(1, 'Email is required').email('Enter a valid email address'),
      password: z.string().min(8, 'Password must be at least 8 characters'),
      confirmPassword: z.string().min(1, 'Please confirm your password'),
    })
    .refine((data) => data.password === data.confirmPassword, {
      message: 'Passwords do not match',
      path: ['confirmPassword'],
    })

  it('validates a valid login payload', () => {
    const valid = loginSchema.safeParse({
      email: 'admin@dockscope.io',
      password: 'StrongPassword123!',
    })
    expect(valid.success).toBe(true)
  })

  it('rejects an invalid email format', () => {
    const invalid = loginSchema.safeParse({
      email: 'invalid-email-string',
      password: 'StrongPassword123!',
    })
    expect(invalid.success).toBe(false)
    if (!invalid.success) {
      expect(invalid.error.issues[0].message).toBe('Enter a valid email address')
    }
  })

  it('rejects a password shorter than 8 characters', () => {
    const invalid = loginSchema.safeParse({
      email: 'admin@dockscope.io',
      password: 'short',
    })
    expect(invalid.success).toBe(false)
    if (!invalid.success) {
      expect(invalid.error.issues[0].message).toBe('Password must be at least 8 characters')
    }
  })

  it('rejects mismatched registration passwords', () => {
    const mismatched = registerSchema.safeParse({
      email: 'admin@dockscope.io',
      password: 'StrongPassword123!',
      confirmPassword: 'DifferentPassword456!',
    })
    expect(mismatched.success).toBe(false)
    if (!mismatched.success) {
      expect(mismatched.error.issues[0].message).toBe('Passwords do not match')
    }
  })

  it('accepts valid registration passwords that match', () => {
    const matching = registerSchema.safeParse({
      email: 'admin@dockscope.io',
      password: 'StrongPassword123!',
      confirmPassword: 'StrongPassword123!',
    })
    expect(matching.success).toBe(true)
  })
})
