import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import BaseInput from '@/components/common/BaseInput.vue'

describe('BaseInput', () => {
  it('renders label and input properly', () => {
    const wrapper = mount(BaseInput, {
      props: {
        modelValue: '',
        label: 'Email Address',
        id: 'test-email',
      },
    })
    expect(wrapper.find('label').text()).toContain('Email Address')
    expect(wrapper.find('input').attributes('id')).toBe('test-email')
  })

  it('emits update:modelValue on input', async () => {
    const wrapper = mount(BaseInput, {
      props: {
        modelValue: '',
      },
    })
    const input = wrapper.find('input')
    await input.setValue('test@dockscope.io')
    expect(wrapper.emitted('update:modelValue')?.[0]).toEqual(['test@dockscope.io'])
  })

  it('renders error message when error prop is provided', () => {
    const wrapper = mount(BaseInput, {
      props: {
        modelValue: '',
        error: 'Invalid email address',
      },
    })
    expect(wrapper.text()).toContain('Invalid email address')
    expect(wrapper.find('input').classes()).toContain('border-dock-danger')
  })
})
